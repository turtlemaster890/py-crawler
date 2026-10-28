from dataclasses import dataclass
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from party import Party
    from combatHandler import CombatHandler
    from player import Player
    from room import Room

type CombatAction = Callable[[Player, CombatHandler], Any]
type PartyAction = Callable[[Party, Room], CombatHandler | Any]
type PlayerAction = Callable[[Party, Player], Any]


@dataclass
class CombatActionEntry:
    name: str
    action: CombatAction
    description: str = ""
    stamina_cost: int = 0
