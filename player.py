from maze import Pos
from inventory import PlayerInventory
from item import Item
from typing import TYPE_CHECKING
if TYPE_CHECKING:   
    from party import Party
    from combatHandler import CombatHandler

class Player:
    def __init__(self, pos: Pos, name: str = "Player", speed: int = 100):
        self.pos = pos
        self.speed = speed
        self.max_health = 100
        self.health = self.max_health
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.name = name
        self.inventory = PlayerInventory()

    def turnStart(self, handler: CombatHandler):
        input()

    def moveItemToParty(self, party: Party, item: Item) -> bool:
        if item not in self.inventory: return False
        if not self.inventory.remove(item): return False
        if not party.inventory.add(item):
            self.inventory.add(item)
            return False
        return True
        