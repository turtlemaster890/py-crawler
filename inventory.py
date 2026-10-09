from item import Item, Weapon

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

    def add(self, item: Item) -> bool:
        if isinstance(item, Weapon): return False
        return super().add(item)