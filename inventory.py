from item import Armor, Item, Weapon
import item


class Inventory:
    def __init__(self, items: list[Item] | None = None):
        self.items: list[Item] = items or []

    def to_json(self):
        return {
            "inventory_type": "inventory",
            "items": [i.to_json() for i in self.items],
        }

    @classmethod
    def from_json(cls, j):
        return cls([Item.from_json(i) for i in j["items"]])

    def __contains__(self, item):
        return item in self.items

    def __getitem__(self, key):
        return self.items[key]

    def add(self, item: Item) -> bool:
        self.items.append(item)
        return True

    def remove(self, item: Item) -> bool:
        if item not in self.items:
            return False
        self.items.remove(item)
        return True


class PlayerInventory(Inventory):
    def __init__(self, items: list[Item] | None = None):
        super().__init__()
        self.weapon: Weapon | None = None
        self.armor: Armor | None = None

    def to_json(self):
        j = super().to_json()
        j["inventory_type"] = "player_inventory"
        j["weapon"] = self.weapon.to_json() if self.weapon else None
        j["armor"] = self.armor.to_json() if self.armor else None
        return j

    @classmethod
    def from_json(cls, j):
        new_player_inventory = super().from_json(j)
        new_player_inventory.weapon = item.from_json(j["weapon"])
        new_player_inventory.armor = item.from_json(j["armor"])
        return new_player_inventory

    def add(self, item: Item) -> bool:
        if isinstance(item, Weapon):
            return False
        if isinstance(item, Armor):
            return False
        return super().add(item)

    def equip(self, item: Item) -> Item | None:
        if not isinstance(item, (Weapon, Armor)):
            return None
        if isinstance(item, Weapon):
            equiped_weapon = self.weapon
            self.weapon = item
            return equiped_weapon
        if isinstance(item, Armor):
            equiped_armor = self.armor
            self.armor = item
            return equiped_armor


inventory_type_to_class = {"inventory": Inventory, "player_inventory": PlayerInventory}


def from_json(j):
    _class = inventory_type_to_class[j["inventory_type"]]
    return _class.from_json(j)
