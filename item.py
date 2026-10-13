class Item:
    def __init__(
        self,
        name: str,
    ):
        self.name = name

    def to_json(self) -> dict[str, object]:
        return {"item_type": "item", "name": self.name}

    @classmethod
    def from_json(cls, j):
        return cls(j["name"])


class Weapon(Item):
    def __init__(
        self,
        name: str,
    ):
        super().__init__(name)
        self.damage = 5

    def to_json(self):
        j = super().to_json()
        j["item_type"] = "weapon"
        j["damage"] = self.damage
        return j

    @classmethod
    def from_json(cls, j):
        new_item = super().from_json(j)
        new_item.damage = j["damage"]
        return new_item


class Armor(Item):
    def __init__(
        self,
        name: str,
    ):
        super().__init__(name)

    def to_json(self) -> dict[str, object]:
        j = super().to_json()
        j["item_type"] = "armor"
        return j


class Relic(Item):
    def __init__(
        self,
        name: str,
    ):
        self.combat = None
        self.player = None
        super().__init__(name)

    def to_json(self) -> dict[str, object]:
        j = super().to_json()
        j["item_type"] = "relic"
        return j

    def combatStart(self, handler = None):
        self.combat = handler

    def turnStart(self):
        pass

    def turnEnd(self):
        pass

    def healthChange(self, amount, attacker = None, defender = None, damage_type = None):
        pass

    def die(self):
        pass

    def dealDamage(self, amount, attacker = None, defender = None, damage_type = None):
        pass

    def enemyDeath(self, enemy):
        pass

    def inflictCondition(self, condition, target):
        pass

    def equip(self, player):
        self.player = player
        pass

    def unequip(self, player):
        self.player = None
        pass




class Consumable(Item):
    def __init__(
        self,
        name: str,
    ):
        super().__init__(name)

    def to_json(self) -> dict[str, object]:
        j = super().to_json()
        j["item_type"] = "consumable"
        return j


item_type_to_class = {
    "item": Item,
    "weapon": Weapon,
    "armor": Armor,
    "relic": Relic,
    "consumable": Consumable,
}


def from_json(j: dict[str, object]):
    _class = item_type_to_class.get(j["item_type"], Item)  # type: ignore
    return _class.from_json(j)
