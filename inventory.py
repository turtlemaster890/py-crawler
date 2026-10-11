from item import Armor, Item, Weapon, Consumable, Relic

class Inventory:
    def __init__(self):
        self.items: list[Item] = []

    def __contains__(self, item):
        return item in self.items

    def __getitem__(self, key):
        return self.items[key]

    def add(self, item: Item) -> bool:
        self.items.append(item)
        return True

    def remove(self, item: Item) -> bool:
        if item not in self.items: return False
        self.items.remove(item)
        return True

class PlayerInventory(Inventory):
    def __init__(self):
        super().__init__()
        self.weapon: Weapon | None = None
        self.armor: Armor | None = None

    def add(self, item: Item) -> bool:
        if isinstance(item, Weapon ): return False
        if isinstance(item, Armor ): return False
        return super().add(item)

    def equip(self, item: Item) -> Item | None:
        if not isinstance(item, (Weapon, Armor)): return None
        if isinstance(item, Weapon):
            equiped_weapon = self.weapon
            self.weapon = item
            return equiped_weapon
        if isinstance(item, Armor):
            equiped_armor = self.armor
            self.armor = item
            return equiped_armor