import random
from typing import TYPE_CHECKING, Self

from actions import CombatActionEntry, PartyAction, PlayerAction
from conditions import Condition, Slimed
import terminalDisplay
import utils

if TYPE_CHECKING:
    from player import Player
    from party import Party
    from enemy import Enemy
    from combatHandler import CombatHandler


class Item:
    item_type: str = "item"
    description: str = ""

    player_actions: list[tuple[str, PlayerAction]] = []
    party_actions: list[tuple[str, PartyAction]] = []
    combat_actions: list[CombatActionEntry] = []

    def __init__(
        self,
        name: str,
    ) -> None:
        self.name: str = name

    def to_json(self) -> dict[str, object]:
        return {"item_type": self.item_type, "name": self.name}

    @classmethod
    def from_json(cls, j) -> Self:
        return cls(j["name"])


class RustyCoin(Item):
    item_type = "rustyCoin"
    description = "A coin. It is shiny on one side, and tarnished on the other."

    def __init__(self, name: str = "Rusty Coin") -> None:
        super().__init__(name)
        self.player_actions = [("Flip", self.flip)]

    def flip(self, party: Party, player: Player) -> bool:
        heads: bool = random.randint(0, 1) == 1
        terminalDisplay.contextDisplay.print_boxify(
            f"{player.name} flips the {self.name}. It lands on {"heads" if heads else "tails"}."
        )
        utils.wait_for_enter()
        if heads:
            terminalDisplay.contextDisplay.print_boxify(
                f"The shiny face glows slightly, as the coin begins to flake away into shimmers of light. "
                f"{player.name} suddenly feels very fast."
            )
            player.speed += 20
            utils.wait_for_enter()
        else:
            terminalDisplay.contextDisplay.print_boxify(
                f"The tarnished side seems to melt in {player.name}'s hand, as the coin fades away into nothingness."
                f"{player.name} feels a slight twinge in their hand."
            )
            player.health -= 1
            utils.wait_for_enter()
        player.inventory.remove(self)
        return True


class SlimeBall(Item):
    item_type = "slimeball"

    def __init__(self, name: str = "Slimeball") -> None:
        super().__init__(name)
        self.combat_actions = [CombatActionEntry(f"Throw {self.name}", self.throw)]

    def throw(self, player: Player, combatHandler: CombatHandler) -> None:
        target: Player | Enemy = combatHandler.select_character(
            lambda c: isinstance(c, Enemy)
        )[0]
        assert isinstance(target, Enemy)
        target.applyCondition(Slimed(3, target, combatHandler), combatHandler)


class Weapon(Item):
    item_type = "weapon"

    def __init__(
        self,
        name: str,
    ) -> None:
        super().__init__(name)
        self.damage = 5

    def to_json(self) -> dict[str, object]:
        j: dict[str, object] = super().to_json()
        j["damage"] = self.damage
        return j

    @classmethod
    def from_json(cls, j) -> Self:
        new_item: Self = super().from_json(j)
        new_item.damage = j["damage"]
        return new_item


class Bone(Weapon):
    item_type: str = "bone"

    def __init__(self, name: str = "Bone") -> None:
        super().__init__(name)
        self.damage = 7


class Staff(Weapon):
    item_type: str = "staff"

    def __init__(self, name: str = "Staff") -> None:
        super().__init__(name)
        self.damage = 3
        self.combat_actions = [
            CombatActionEntry("Fireball", self.fireball, "High single-target damage", 5)
        ]

    def fireball(self, player: Player, handler: CombatHandler):
        from player import Player

        to_attack: Player | Enemy = handler.select_character(
            lambda c: not isinstance(c, Player)
        )[0]
        damage: int = self.damage * 2
        for item in player.inventory.items:
            if isinstance(item, Relic):
                damage = item.dealDamage(damage, player, to_attack, "magic") or damage
        to_attack.takeDamage(handler, damage, player)


class Armor(Item):
    item_type = "armor"

    def __init__(
        self,
        name: str,
    ) -> None:
        super().__init__(name)


class Relic(Item):
    item_type = "relic"

    def __init__(
        self,
        name: str,
    ) -> None:
        self.combat: CombatHandler | None = None
        self.player: Player | None = None
        super().__init__(name)

    def combatStart(self, handler: CombatHandler | None = None) -> None:
        self.combat = handler

    def turnStart(self) -> None:
        pass

    def turnEnd(self) -> None:
        pass

    def takeDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        pass

    def die(self) -> None:
        pass

    def dealDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        pass

    def enemyDeath(self, enemy: Player | Enemy) -> None:
        pass

    def inflictCondition(self, condition: Condition, target: Player | Enemy) -> None:
        pass

    def equip(self, player: Player) -> None:
        self.player = player

    def unequip(self, player: Player) -> None:
        self.player = None


class Consumable(Item):
    item_type = "consumable"

    def __init__(
        self,
        name: str,
    ) -> None:
        super().__init__(name)


class HealthPotion(Consumable):
    item_type = "healthPotion"

    def __init__(self, name: str = "Health Potion") -> None:
        super().__init__(name)
        self.player_actions = [("Drink", self.drink)]
        self.combat_actions = [CombatActionEntry("Drink potion", self.drink_combat)]

    def drink(self, party: Party, player: Player) -> bool:
        player.health = min(player.max_health, player.health + 30)
        terminalDisplay.contextDisplay.print_boxify(
            f"{player.name} drinks the {self.name}."
        )
        utils.wait_for_enter()
        player.inventory.remove(self)
        return True

    def drink_combat(self, player: Player, handler: CombatHandler) -> None:
        self.drink(handler.party, player)


class ManaBooster(Relic):
    item_type: str = "manaBooster"
    description = "Magic damage deals +2"

    def __init__(self, name: str = "Mana Booster") -> None:
        super().__init__(name)

    def dealDamage(
        self, amount, attacker=None, defender=None, damage_type=None
    ) -> int | None:
        if damage_type == "magic":
            return amount + 2


class ThornedAmulet(Relic):
    item_type: str = "thornedAmulet"
    description = "Returns 25% damage to attacker"

    def __init__(self, name: str = "Thorned Amulet") -> None:
        super().__init__(name)

    def takeDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        if attacker and self.combat:
            return_damage: int = max(1, int(amount * 0.25))
            attacker.takeDamage(self.combat, return_damage, self.player)


class QuickBoots(Relic):
    item_type: str = "quickBoots"
    description = "+10 speed"

    def __init__(self, name: str = "Quick Boots") -> None:
        super().__init__(name)

    def equip(self, player: Player) -> None:
        super().equip(player)
        player.speed += 10

    def unequip(self, player) -> None:
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
    "rustyCoin": RustyCoin,
    "bone": Bone,
    "staff": Staff,
    "healthPotion": HealthPotion
}


def from_json(j: dict[str, object]):
    _class = item_type_to_class.get(j["item_type"], Item)  # type: ignore
    return _class.from_json(j)
