from dataclasses import dataclass
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from party import Party
    from combatHandler import CombatHandler
    from player import Player

type CombatAction = Callable[[Player, CombatHandler], None]
type PartyAction = Callable[[Party], CombatHandler | Any]
type PlayerAction = Callable[[Party, Player], Any]


@dataclass
class CombatActionEntry:
    name: str
    action: CombatAction
    description: str = ""
    stamina_cost: int = 0
