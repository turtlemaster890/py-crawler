from dataclasses import dataclass
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from player import Player
    from enemy import enemy

@dataclass
class TurnEntry:
    av: float
    character: Player | enemy