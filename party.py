from maze import Pos
from player import Player
from inventory import Inventory
from item import Item
from inventory import Inventory, PlayerInventory

class Party:
    def __init__(self, pos: Pos, members: list[Player]):
        self.pos = pos
        self.members = members
        self.inventory = Inventory()
        self.funds = 0

    def moveItemToMember(self, member: Player, item: Item) -> bool:
        if item not in self.inventory: return False
        if not self.inventory.remove(item): return False
        if not member.inventory.add(item):
            self.inventory.add(item)
            return False
        return True