from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from party import Party
    from combatHandler import CombatHandler
    from player import Player

type CombatAction = Callable[[CombatHandler], None]
type PartyAction = Callable[[Party], CombatHandler | None]
type PlayerAction = Callable[[Party, Player], Any]
