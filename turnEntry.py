from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from enemy import Enemy


@dataclass
class TurnEntry:
    av: float
    character: Player | Enemy
