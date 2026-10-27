from typing import Any, Protocol, TYPE_CHECKING

from combatHandler import CombatHandler
import time

from enemy import enemy
from party import Party
from squad import Squad
from turnEntry import TurnEntry

if TYPE_CHECKING:
    from player import Player


class NotifyProtocol(Protocol):
    def __call__(self, msg: dict[str, Any], members: list[Any] = ...) -> None: ...


class NetworkCombatHandler(CombatHandler):
    def __init__(
        self,
        party: Party,
        players: list[Player],
        enemies: list[enemy],
        notify: NotifyProtocol,
        pause_seconds: float,
    ):
        self.notify = notify
        self.pause_seconds = pause_seconds
        self.current_player: Player | None = None
        self.selected_option: int | None = None
        super().__init__(party, players, enemies)

    def announce(self, text: str, typed: bool = False):
        self.notify({"type": "log", "text": text, "typed": typed})

    def pause(self):
        time.sleep(self.pause_seconds)

    def refresh(self):
        self.notify(self.state_message())

    def state_message(self):
        return {
            "type": "combat_state",
            "turn_order": [
                {
                    "name": entry.character.name,
                    "health": entry.character.health,
                    "av": round(entry.av),
                    "is_player": entry.character in self.players,
                }
                for entry in self.turn_order
            ],
        }

    def offer_action(self, squad: Squad, option: int):
        if self.current_player in squad.characters:
            self.selected_option = option

    def choose_action(self, player: Player, options: list[str]) -> int:
        self.current_player = player
        self.notify({"type": "choose_option", "options": options}, [player])
        while self.selected_option is None:
            time.sleep(0.01)
        r = self.selected_option
        self.selected_option = None
        self.current_player = None
        return r

    def choose_targets(self, options: list[TurnEntry], count: int, minimum: int) -> list[int]:
        return list(range(min(count, len(options))))
