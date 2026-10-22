import sys

from pynput.keyboard import Key

import terminalDisplay
import inputController
from typing import TYPE_CHECKING, Callable
from turnEntry import TurnEntry
import utils

if TYPE_CHECKING:
    from player import Player
    from enemy import Enemy
    from party import Party
    from item import Item


class CombatHandler:
    def __init__(
        self,
        party: Party,
        players: list[Player] | None = None,
        enemies: list[Enemy] | None = None,
    ):
        self.party = party
        self.players = players or []
        self.enemies = enemies or []
        self.turn_order: list[TurnEntry] = []
        for character in self.players + self.enemies:
            av: float = 10000 / character.speed
            self.turn_order.append(TurnEntry(av, character))
        self.turn_order.sort(key=lambda x: x.av)
        for i in range(1, len(self.turn_order)):
            self.turn_order[i].av -= self.turn_order[0].av
        self.turn_order[0].av = 0
        terminalDisplay.combatDisplay.messageProvider = self.print_turn_order_list
        for enemy in self.enemies:
            enemy.combatStart(self)

    def addEnemy(self, enemy: Enemy):
        enemy.combatStart(self)
        self.turn_order.append(TurnEntry(10000 / enemy.speed, enemy))
        self.enemies.append(enemy)

    def removeEnemy(self, enemy: Enemy):
        for i, entry in enumerate(self.turn_order):
            if entry.character is enemy:
                del self.turn_order[i]
                self.enemies.remove(enemy)
                return

    def removePlayer(self, player: Player):
        for i, entry in enumerate(self.turn_order):
            if entry.character is player:
                del self.turn_order[i]
                self.players.remove(player)
                return

    def combat(self) -> bool:
        if utils.DEBUG:
            self.enemies = []
        if len(self.players) == 0:
            print("YOU LOSE!!!")
            sys.exit()
        if len(self.enemies) == 0:
            for player in self.players:
                player.leaveCombat()
            terminalDisplay.combatDisplay.messageProvider = None
            return False
        terminalDisplay.updateDisplays()
        self.turn_order[0].character.turnStart(self)
        self.tick_initiative()
        return True

    def tick_initiative(self):
        current_av, current_character = (
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

    def select_character(
        self, f: Callable[[Player | Enemy], bool], count: int = 1, minimum: int = -1
    ) -> list[Player | Enemy]:
        if minimum == -1:
            minimum = count
        options = [e for e in self.turn_order if f(e.character)]
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
                            return [option.character for option in selected]
                    # terminalDisplay.combatDisplay.messageProvider = (
                    #     self.print_turn_order_list
                    # )
                    # return [option.character for option in selected]

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

        out = []
        # "│ " (2) + " │ " (3) + " ### AV │" (8) = 13 characters
        nameSpace = w - 14
        maxOptions: int = h - 5

        out.append("┌" + "─" * (w - 2) + "┐")
        out.append(
            "│"
            + f"TURN ORDER (Select {f"{minimum}-{count}" if minimum < count else minimum})".center(
                w - 2
            )
            + "│"
        )
        out.append("├" + "─" * (w - 2) + "┤")
        realOptions = -1
        start_point = 0
        realHovered = len(self.turn_order)
        if hovered < len(options):
            realHovered = self.turn_order.index(options[hovered])
        if realHovered >= maxOptions:
            start_point = (
                realHovered - maxOptions + (realHovered < len(self.turn_order))
            )
        for i, entry in enumerate(self.turn_order):
            if i < start_point:
                continue
            if i >= start_point + maxOptions:
                continue
            if entry in options:
                realOptions += 1
            sel_str = (
                ">["
                if (i == realHovered and entry in options and entry in selected)
                else (
                    " ["
                    if (entry in options and entry in selected)
                    else (
                        "> "
                        if i == realHovered and entry in options
                        else ("  " if entry in options else " ")
                    )
                )
            )
            sel_extra = "]" if entry in options and entry in selected else " "
            name = (
                (entry.character.name + f" ({entry.character.health}♥)")[
                    : nameSpace - len(sel_extra)
                ]
                + sel_extra
            ).ljust(nameSpace - (len(sel_str) - 2))
            av_str = f"{entry.av:<3.0f}"
            out.append(f"│{sel_str}{name} │ {av_str} AV │")
        out.append(
            f"│{"> " if hovered == len(options) else "  "}{"Confirm".ljust(w - 4)}│"
        )
        out.append("└" + "─" * (w - 2) + "┘")
        return out
