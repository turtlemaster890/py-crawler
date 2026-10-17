class Item:
    item_type = "item"
    description = ""

    def __init__(
        self,
        name: str,
    ):
        self.name = name

    def to_json(self) -> dict[str, object]:
        return {"item_type": self.item_type, "name": self.name}

    @classmethod
    def from_json(cls, j):
        return cls(j["name"])


class Weapon(Item):
    item_type = "weapon"

    def __init__(
        self,
        name: str,
    ):
        super().__init__(name)
        self.damage = 5

    def to_json(self):
        j = super().to_json()
        j["damage"] = self.damage
        return j

    @classmethod
    def from_json(cls, j):
        new_item = super().from_json(j)
        new_item.damage = j["damage"]
        return new_item


class Armor(Item):
    item_type = "armor"

    def __init__(
        self,
        name: str,
    ):
        super().__init__(name)


class Relic(Item):
    item_type = "relic"

    def __init__(
        self,
        name: str,
    ):
        self.combat = None
        self.player = None
        super().__init__(name)

    def combatStart(self, handler=None):
        self.combat = handler

    def turnStart(self):
        pass

    def turnEnd(self):
        pass

    def takeDamage(self, amount, attacker=None, defender=None, damage_type=None):
        pass

    def die(self):
        pass

    def dealDamage(self, amount, attacker=None, defender=None, damage_type=None):
        pass

    def enemyDeath(self, enemy):
        pass

    def inflictCondition(self, condition, target):
        pass

    def equip(self, player):
        self.player = player

    def unequip(self, player):
        self.player = None


class Consumable(Item):
    item_type = "consumable"

    def __init__(
        self,
        name: str,
    ):
        super().__init__(name)


class ManaBooster(Relic):
    item_type = "manaBooster"
    description = "Magic damage deals +2"

    def __init__(self, name: str = "Mana Booster"):
        super().__init__(name)

    def dealDamage(self, amount, attacker=None, defender=None, damage_type=None):
        if damage_type == "magic":
            return amount + 2


class ThornedAmulet(Relic):
    item_type = "thornedAmulet"
    description = "Returns 25% damage to attacker"

    def __init__(self, name: str = "Thorned Amulet"):
        super().__init__(name)

    def takeDamage(self, amount, attacker=None, defender=None, damage_type=None):
        if attacker:
            return_damage = max(1, int(amount * 0.25))
            attacker.takeDamage(self.combat, return_damage, self.player)


class QuickBoots(Relic):
    item_type = "quickBoots"
    description = "+10 speed"

    def __init__(self, name: str = "Quick Boots"):
        super().__init__(name)

    def equip(self, player):
        super().equip(player)
        player.speed += 10

    def unequip(self, player):
        super().unequip(player)
        player.speed -= 10


item_type_to_class = {
    "item": Item,
    "weapon": Weapon,
    "armor": Armor,
    "relic": Relic,
    "consumable": Consumable,
    "manaBooster": ManaBooster,
    "thornedAmulet": ThornedAmulet,
    "quickBoots": QuickBoots,
}


def from_json(j: dict[str, object]):
    _class = item_type_to_class.get(j["item_type"], Item)  # type: ignore
    return _class.from_json(j)
