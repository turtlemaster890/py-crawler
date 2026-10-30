from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING

import menuHelper
import terminalDisplay
import utils
from actions import CombatActionEntry
from turnEntry import TurnEntry

if TYPE_CHECKING:
    from enemy import Enemy
    from party import Party
    from player import Player


class CombatResult(Enum):
    CONTINUE = 1
    VICTORY = 2
    DEFEAT = 3


class CombatHandler:
    def __init__(
        self,
        party: Party,
        players: list[Player] | None = None,
        enemies: list[Enemy] | None = None,
    ):
        self.victory = False
        self.party = party
        self.players = players or []
        self.enemies = enemies or []
        for enemy in self.enemies:
            enemy.combatStart(self)
        for player in self.players:
            player.startCombat(self)
        self.turn_order: list[TurnEntry] = []
        for character in self.players + self.enemies:
            av: float = 10000 / character.speed
            self.turn_order.append(TurnEntry(av, character))
        self.turn_order.sort(key=lambda x: x.av)
        for i in range(1, len(self.turn_order)):
            self.turn_order[i].av -= self.turn_order[0].av
        self.turn_order[0].av = 0
        terminalDisplay.combatDisplay.messageProvider = self.print_turn_order_list

    def addEnemy(self, enemy: Enemy):
        enemy.scale(self.party.floor)
        enemy.combatStart(self)
        self.turn_order.append(TurnEntry(10000 / enemy.speed, enemy))
        self.enemies.append(enemy)

    def removeEnemy(self, enemy: Enemy):
        for i, entry in enumerate(self.turn_order[:]):
            if entry.character is enemy:
                del self.turn_order[i]
                self.enemies.remove(enemy)
                return

    def removePlayer(self, player: Player):
        for i, entry in enumerate(self.turn_order[:]):
            if entry.character is player:
                del self.turn_order[i]
                self.players.remove(player)
                return

    def choose_action(
        self,
        player: Player,
        options: list[CombatActionEntry],
    ) -> int:

        return menuHelper.menu(
            "",
            [opt.name for opt in options],
            False,
            terminalDisplay.contextDisplay,
            lambda sel: (
                terminalDisplay.contextDisplay.print_boxify(options[sel].description)
                if options[sel].description
                else None
            ),
        )

        # selected_option = 0
        # lastProvider = terminalDisplay.contextDisplay.messageProvider
        # terminalDisplay.contextDisplay.messageProvider = (
        #     lambda w, h: player.pretty_print_turn_options(
        #         options, selected_option, w, h
        #     )
        # )
        # lastDescProvider = terminalDisplay.descriptionDisplay.messageProvider
        # terminalDisplay.descriptionDisplay.messageProvider = lambda w, h: (
        #     utils.boxify(w, h, options[selected_option].description)  # type: ignore
        #     if options[selected_option].description
        #     else []
        # )
        # while True:
        #     selected_option %= len(options)
        #     terminalDisplay.updateDisplays()
        #     while True:
        #         key = inputController.getKey()
        #         if key in utils.key_to_delta:
        #             selected_option += utils.key_to_delta[key]
        #             break
        #         if key == Key.enter:
        #             terminalDisplay.contextDisplay.messageProvider = lastProvider
        #             terminalDisplay.descriptionDisplay.messageProvider = (
        #                 lastDescProvider
        #             )
        #             return selected_option

    def combat(self) -> CombatResult:
        if utils.DEBUG_END_COMBAT:
            self.enemies = []
        if len(self.players) == 0:
            return CombatResult.DEFEAT
        if len(self.enemies) == 0:
            for player in self.players:
                player.leaveCombat()
            terminalDisplay.combatDisplay.messageProvider = None
            return CombatResult.VICTORY
        self.refresh()
        self.turn_order[:][0].character.turnStart(self)
        self.tick_initiative()
        return CombatResult.CONTINUE

    def tick_initiative(self):
        _current_av, current_character = (
            self.turn_order[0].av,
            self.turn_order[0].character,
        )

        next_av = 10000 / current_character.speed
        self.turn_order[0].av = next_av
        self.turn_order.sort(key=lambda x: x.av)

        for i in range(1, len(self.turn_order)):
            self.turn_order[i].av -= self.turn_order[0].av
        self.turn_order[0].av = 0

    def print_turn_order(self):
        longestName = max(len(entry.character.name) for entry in self.turn_order)
        additionalChars = max(0, longestName - 15)
        print("┌──────────────────────────" + "─" * additionalChars + "┐")
        print("│" + "TURN ORDER".center(26 + additionalChars) + "│")
        print("├──────────────────────────" + "─" * additionalChars + "┤")
        for entry in self.turn_order:
            print(
                f"│ {entry.character.name.ljust(15 + additionalChars)} │ {entry.av:<3.0f} AV │"
            )
        print("└──────────────────────────" + "─" * additionalChars + "┘")

    def print_turn_order_list(self, w: int, h: int) -> list[str]:
        out = []
        # "│ " (2) + " │ " (3) + " ### AV │" (8) = 13 characters
        nameSpace = w - 13

        out.append("┌" + "─" * (w - 2) + "┐")
        out.append("│" + "TURN ORDER".center(w - 2) + "│")
        out.append("├" + "─" * (w - 2) + "┤")
        for entry in self.turn_order:
            name = (entry.character.name + f" ({entry.character.health}♥)")[
                :nameSpace
            ].ljust(nameSpace)
            av_str = f"{entry.av:<3.0f}"
            out.append(f"│ {name} │ {av_str} AV │")
        out.append("└" + "─" * (w - 2) + "┘")
        return out

    def choose_targets(
        self, player: Player, options: list[TurnEntry], count: int, minimum: int
    ) -> list[int]:
        from pynput.keyboard import Key

        import inputController

        hovered = 0
        selected: list[TurnEntry] = []
        terminalDisplay.combatDisplay.messageProvider = (
            lambda w, h: self.print_turn_order_list_select(
                w, h, selected, hovered, options, count, minimum
            )
        )
        while True:
            hovered %= len(options) + 1
            terminalDisplay.updateDisplays()
            while True:
                key = inputController.getKey()
                if key in utils.key_to_delta:
                    hovered += utils.key_to_delta[key]
                    break
                if key == Key.enter:
                    if hovered < len(options):
                        if options[hovered] in selected:
                            selected.remove(options[hovered])
                        elif len(selected) < count:
                            selected.append(options[hovered])
                        break
                    else:
                        if len(selected) >= minimum:
                            terminalDisplay.combatDisplay.messageProvider = (
                                self.print_turn_order_list
                            )
                            return [options.index(e) for e in selected]

    def select_character(
        self,
        player: Player,
        f: Callable[[Player | Enemy], bool],
        count: int = 1,
        minimum: int = -1,
    ) -> list[Player | Enemy]:
        if minimum == -1:
            minimum = count
        options = [e for e in self.turn_order if f(e.character)]
        chosen = self.choose_targets(player, options, count, minimum)
        return [options[i].character for i in chosen]

    def print_turn_order_list_select(
        self,
        w: int,
        h: int,
        selected: list[TurnEntry],
        hovered: int,
        options: list[TurnEntry],
        count: int,
        minimum: int,
    ) -> list[str]:
        return print_turn_order_list_select(
            w, h, self.turn_order, selected, hovered, options, count, minimum
        )

    def announce(self, text: str, typed: bool = False):
        if typed == True:
            terminalDisplay.contextDisplay.type_print(text)
        else:
            terminalDisplay.contextDisplay.print_boxify(text)

    def pause(self):
        utils.wait_for_enter()

    def refresh(self):
        terminalDisplay.updateDisplays()


def choose_targets(
    entries: list[TurnEntry], options: list[TurnEntry], count: int, minimum: int
) -> list[int]:
    from pynput.keyboard import Key

    import inputController

    hovered = 0
    selected: list[TurnEntry] = []
    lastProvider = terminalDisplay.combatDisplay.messageProvider
    terminalDisplay.combatDisplay.messageProvider = (
        lambda w, h: print_turn_order_list_select(
            w, h, entries, selected, hovered, options, count, minimum
        )
    )
    while True:
        hovered %= len(options) + 1
        terminalDisplay.updateDisplays()
        while True:
            key = inputController.getKey()
            if key in utils.key_to_delta:
                hovered += utils.key_to_delta[key]
                break
            if key == Key.enter:
                if hovered < len(options):
                    if options[hovered] in selected:
                        selected.remove(options[hovered])
                    elif len(selected) < count:
                        selected.append(options[hovered])
                    break
                else:
                    if len(selected) >= minimum:
                        terminalDisplay.combatDisplay.messageProvider = lastProvider
                        return [options.index(e) for e in selected]


def print_turn_order_list_select(
    w: int,
    h: int,
    entries: list[TurnEntry],
    selected: list[TurnEntry],
    hovered: int,
    options: list[TurnEntry],
    count: int,
    minimum: int,
) -> list[str]:
    out = []
    nameSpace = w - 14
    maxOptions = h - 5

    out.append("┌" + "─" * (w - 2) + "┐")
    out.append(
        "│"
        + f"TURN ORDER (Select {f"{minimum}-{count}" if minimum < count else minimum})".center(
            w - 2
        )
        + "│"
    )
    out.append("├" + "─" * (w - 2) + "┤")
    realHovered = len(entries)
    if hovered < len(options):
        realHovered = entries.index(options[hovered])
    start = 0
    if realHovered >= maxOptions:
        start = realHovered - maxOptions + (realHovered < len(entries))
    for i, entry in enumerate(entries):
        if i < start or i >= start + maxOptions:
            continue
        opt = entry in options
        sel = entry in selected
        sel_str = (
            ">["
            if (i == realHovered and opt and sel)
            else (
                " ["
                if (opt and sel)
                else ("> " if (i == realHovered and opt) else ("  " if opt else " "))
            )
        )
        sel_extra = "]" if opt and sel else " "
        name = (
            (entry.character.name + f" ({entry.character.health}♥)")[
                : nameSpace - len(sel_extra)
            ]
            + sel_extra
        ).ljust(nameSpace - (len(sel_str) - 2))
        av_str = f"{entry.av:<3.0f}"
        out.append(f"│{sel_str}{name} │ {av_str} AV │")
    out.append(f"│{"> " if hovered == len(options) else "  "}{"Confirm".ljust(w - 4)}│")
    out.append("└" + "─" * (w - 2) + "┘")
    return out
