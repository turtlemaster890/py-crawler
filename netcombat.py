import time
from typing import TYPE_CHECKING, Protocol

from actions import CombatActionEntry
from combatHandler import CombatHandler, CombatResult
from enemy import AggroEntry, Enemy
from packets import (
    ChoiceRow,
    ChooseCharacters,
    ChooseOption,
    CombatState,
    Log,
    Packet,
    TurnRow,
)
from party import Party
from squad import Squad
from turnEntry import TurnEntry

if TYPE_CHECKING:
    from player import Player


class NotifyProtocol(Protocol):
    def __call__(self, msg: Packet, members: list[Player] | None = None) -> None: ...


class PlayerLeft(Exception):
    pass


class NetworkCombatHandler(CombatHandler):
    def __init__(
        self,
        party: Party,
        players: list[Player],
        enemies: list[Enemy],
        notify: NotifyProtocol,
        pause_seconds: float,
    ):
        self.notify = notify
        self.pause_seconds = pause_seconds
        self.current_player: Player | None = None
        self.selected_option: int | None = None
        self.selected_options: list[int] | None = None
        self._joining: list[Player] = []
        self.leaving: list[Player] = []
        super().__init__(party, players, enemies)

    def announce(self, text: str, typed: bool = False):
        self.notify(Log(text, typed))

    def pause(self):
        time.sleep(self.pause_seconds)

    def refresh(self):
        self.notify(self.state_message())

    def state_message(self) -> Packet:
        return CombatState(
            [
                TurnRow(
                    e.character.name,
                    e.character.health,
                    round(e.av),
                    e.character in self.players,
                )
                for e in self.turn_order
            ]
        )

    def add_players(self, players: list[Player]):
        self._joining.extend(players)

    def remove_players_later(self, players: list[Player]):
        self.leaving.extend(players)

    def _apply_pending(self):
        while self._joining:
            p = self._joining.pop(0)
            if p in self.players:
                continue
            self.players.append(p)
            p.startCombat(self)
            self.turn_order.append(TurnEntry(10000 / p.speed, p))
            for e in self.enemies:
                e.aggro.append(AggroEntry(0, p))
        for p in list(self.leaving):
            if p in self.players:
                self.removePlayer(p)
            p.leaveCombat()
            if p.health <= 0:
                p.health = p.max_health
            self.leaving.remove(p)

    def combat(self) -> CombatResult:
        self._apply_pending()
        try:
            return super().combat()
        except PlayerLeft:
            self._apply_pending()
            return CombatResult.CONTINUE

    def offer_action(self, squad: Squad, option: int):
        if self.current_player in squad.characters:
            self.selected_option = option

    def offer_selection(self, squad: Squad, options: list[int]):
        if self.current_player in squad.characters:
            self.selected_options = options

    def choose_action(
        self,
        player: Player,
        options: list[CombatActionEntry],
    ) -> int:
        self.current_player = player
        self.notify(
            ChooseOption([option.name for option in options]),
            [player],
        )
        self.selected_option = None
        while self.selected_option is None:
            if player in self.leaving:
                self.current_player = None
                raise PlayerLeft
            time.sleep(0.01)
        r = self.selected_option
        self.selected_option = None
        self.current_player = None
        return r

    def choose_targets(
        self, player: Player, options: list[TurnEntry], count: int, minimum: int
    ) -> list[int]:
        if not options:
            return []
        self.current_player = player
        self.notify(self.state_message(), [player])
        self.notify(
            ChooseCharacters(
                [
                    ChoiceRow(e.character.name, e.character.health, round(e.av), i)
                    for i, e in enumerate(self.turn_order)
                    if e in options
                ],
                count,
                minimum,
            ),
            [player],
        )
        self.selected_options = None
        while self.selected_options is None:
            if player in self.leaving:
                self.current_player = None
                raise PlayerLeft
            time.sleep(0.01)
        r = self.selected_options
        self.selected_options = None
        self.current_player = None
        return r
