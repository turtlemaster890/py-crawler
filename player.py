import json
from maze import Pos
from inventory import PlayerInventory
from item import Item
from typing import TYPE_CHECKING
if TYPE_CHECKING:   
    from party import Party
    from combatHandler import CombatHandler

class Player:
    def __init__(self, pos: Pos, name: str = "Player", class_type: str = "warrior"):
        self.pos = pos
        self.name = name
        self.class_type = class_type
        self.inventory = PlayerInventory()

        with open("player_stats.json", "r") as f:
            all_stats: dict[str, dict[str, int]] = json.load(f)
            self.stats = all_stats[self.class_type]

        self.speed = self.stats["base_stats"]["speed"]
        self.max_health = self.stats["base_stats"]["health"]
        self.health = self.max_health
        self.max_stamina = self.stats["base_stats"]["stamina"]
        self.stamina = self.max_stamina
        self.inventory.equip(self.stats["starting_items"]["weapon"])
        self.inventory.equip(self.stats["starting_items"]["armor"])
        for item in self.stats["starting_items"]["items"]:
            self.inventory.add(Item(item))

    def turnStart(self, handler: CombatHandler):
        input()

    def moveItemToParty(self, party: Party, item: Item) -> bool:
        if item not in self.inventory: return False
        if not self.inventory.remove(item): return False
        if not party.inventory.add(item):
            self.inventory.add(item)
            return False
        return True