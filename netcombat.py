from typing import Protocol, TYPE_CHECKING

from actions import CombatActionEntry
from combatHandler import CombatHandler
import time

from enemy import Enemy
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
    def __call__(self, msg: Packet, members: list[Player] = []) -> None: ...


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
        while self.selected_option is None:
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
        time.sleep(0.1)
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
        while self.selected_options is None:
            time.sleep(0.01)
        r = self.selected_options
        self.selected_options = None
        self.current_player = None
        return r
