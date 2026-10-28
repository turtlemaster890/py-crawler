import random
from typing import TYPE_CHECKING, Any, Self

from actions import CombatActionEntry, PartyAction, PlayerAction
from conditions import Condition, Poisoned, Slimed
import terminalDisplay
import utils

if TYPE_CHECKING:
    from player import Player
    from party import Party
    from enemy import Enemy
    from combatHandler import CombatHandler
    from room import Room


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

    def throw(self, player: Player, combatHandler: CombatHandler) -> bool:
        from enemy import Enemy

        target: Player | Enemy = combatHandler.select_character(
            lambda c: isinstance(c, Enemy)
        )[0]
        assert isinstance(target, Enemy)
        target.applyCondition(Slimed(3, target, combatHandler), combatHandler)
        return True


class Key(Item):
    item_type = "key"

    def __init__(self, name: str = "Key") -> None:
        super().__init__(name)
        self.party_actions = [(f"Use {self.name}", self.use)]

    def use(self, party: Party, room: Room):
        from room import LockedRoom

        if isinstance(room, LockedRoom):
            if room.locked:
                room.locked = False
                terminalDisplay.contextDisplay.print_boxify(
                    f"The {self.name} slides perfectly into the lock. You hear a 'click'."
                )
                for connection in room.list_connections():
                    party.discovered_positions.add(party.pos + connection)
                party.inventory.remove(self)
            else:
                terminalDisplay.contextDisplay.print_boxify(
                    "This room is already unlocked!"
                )
        else:
            terminalDisplay.contextDisplay.print_boxify(
                f"The {self.name} can only be used on a locked room."
            )
        utils.wait_for_enter()
        return True


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

    def fireball(self, player: Player, handler: CombatHandler) -> bool:
        from player import Player

        to_attack: Player | Enemy = handler.select_character(
            lambda c: not isinstance(c, Player)
        )[0]
        damage: int = self.damage * 2
        for item in player.inventory.items:
            if isinstance(item, Relic):
                r = item.dealDamage(damage, player, to_attack, "magic")
                if r is not None:
                    damage = r
        to_attack.takeDamage(handler, damage, player)
        return True


class Armor(Item):
    item_type = "armor"

    def __init__(
        self,
        name: str,
    ) -> None:
        super().__init__(name)
        self.defense = 2


class ZombieCrown(Armor):
    item_type = "zombieCrown"

    def __init__(self, name: str = "Zombie Crown") -> None:
        super().__init__(name)
        self.defense = 15


class Relic(Item):
    item_type = "relic"

    def __init__(
        self,
        name: str = "Relic",
    ) -> None:
        self.combat: CombatHandler | None = None
        self.player: Player | None = None
        super().__init__(name)

    def combatStart(self, handler: CombatHandler | None = None) -> None:
        self.combat = handler

    def combatEnd(self) -> None:
        self.combat = None

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

    def drink_combat(self, player: Player, handler: CombatHandler) -> bool:
        return self.drink(handler.party, player)


class AntidoteBottle(Consumable):
    item_type = "antidoteBottle"

    def __init__(self, name: str = "Bottle of Antidote") -> None:
        super().__init__(name)
        self.combat_actions = [CombatActionEntry("Drink Antidote", self.drink)]

    def drink(self, player: Player, handler: CombatHandler) -> bool:
        cond = player.has_condition(Poisoned)
        if cond:
            cond.changeDuration(-cond.duration)
            player.inventory.remove(self)
            terminalDisplay.contextDisplay.print_boxify(
                f"{player.name} drinks the bottle of antidote. They feel more relaxed now."
            )
            utils.wait_for_enter()
            return True
        terminalDisplay.contextDisplay.print_boxify(f"{player.name} isn't poisoned!")
        utils.wait_for_enter()
        return False


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
    description = "+10 speed in combat"

    def __init__(self, name: str = "Quick Boots") -> None:
        super().__init__(name)
        self.active = False

    def combatStart(self, handler: CombatHandler | None = None) -> None:
        super().combatStart(handler)
        if self.player and not self.active:
            self.player.speed += 10
            self.active = True

    def combatEnd(self) -> None:
        if self.player and self.active:
            self.player.speed -= 10
            self.active = False


class AntidoticCharm(Relic):
    item_type: str = "antidoticCharm"
    description = "Prevents damage from poison"

    def __init__(self, name: str = "Antidotic Charm") -> None:
        super().__init__(name)

    def takeDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        if damage_type == "poison":
            return 0


class VampiricFang(Relic):
    item_type: str = "vampiricFang"
    description = "Heal 20% of damage you deal"

    def __init__(self, name: str = "Vampiric Fang") -> None:
        super().__init__(name)

    def dealDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        if attacker is not None:
            attacker.health = min(
                attacker.max_health, attacker.health + max(1, amount // 5)
            )


class BulwarkCharm(Relic):
    item_type: str = "bulwarkCharm"
    description = "Take 1 less damage from a hit"

    def __init__(self, name: str = "Bulwark Charm") -> None:
        super().__init__(name)

    def takeDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        if amount > 1:
            return amount - 1


class BerserkerBand(Relic):
    item_type: str = "berserkerBand"
    description = "+3 damage while at or below half health"

    def __init__(self, name: str = "Berserker Band") -> None:
        super().__init__(name)

    def dealDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        if attacker is not None and attacker.health <= attacker.max_health / 2:
            return amount + 3


class GlassIdol(Relic):
    item_type: str = "glassIdol"
    description = "Deal 50% more damage, take 50% more damage"

    def __init__(self, name: str = "Glass Idol") -> None:
        super().__init__(name)

    def dealDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        return amount * 3 // 2

    def takeDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        return amount * 3 // 2


class ScavengerPurse(Relic):
    item_type: str = "scavengerPurse"
    description = "Enemies drop ¢3-8 when they die"

    def __init__(self, name: str = "Scavenger's Purse") -> None:
        super().__init__(name)

    def enemyDeath(self, enemy: Player | Enemy) -> None:
        if self.combat:
            self.combat.party.funds += random.randint(3, 8)


class PhoenixFeather(Relic):
    item_type: str = "phoenixFeather"
    description = "One revive at 1/3 health"

    def __init__(self, name: str = "Phoenix Feather") -> None:
        super().__init__(name)

    def die(self) -> None:
        p = self.player
        if p and p.health <= 0:
            p.health = max(1, p.max_health // 3)
            p.inventory.remove(self)
            terminalDisplay.contextDisplay.print_boxify(
                f"{p.name}'s {self.name} bursts into flame. They rise again!"
            )
            utils.wait_for_enter()


class VenomRing(Relic):
    item_type: str = "venomRing"
    description = "30% chance to poison what you hit"

    def __init__(self, name: str = "Venom Ring") -> None:
        super().__init__(name)

    def dealDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        if defender is not None and self.combat:
            from conditions import inflict

            inflict(
                {"type": "poisoned", "duration": 3, "chance": 0.3},
                defender,
                self.combat,
            )


class RegenBand(Relic):
    item_type: str = "regenBand"
    description = "Heal 2 health at the start of turn"

    def __init__(self, name: str = "Regen Band") -> None:
        super().__init__(name)

    def turnStart(self) -> None:
        p = self.player
        if p:
            p.health = min(p.max_health, p.health + 2)


class EnergyCrystal(Relic):
    item_type: str = "energyCrystal"
    description = "+2 stamina at start of turn"

    def __init__(self, name: str = "Energy Crystal") -> None:
        super().__init__(name)

    def turnStart(self) -> None:
        p = self.player
        if p:
            p.stamina = min(p.max_stamina, p.stamina + 2)


item_type_to_class: dict[str, type[Item]] = {
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
    "healthPotion": HealthPotion,
    "slimeball": SlimeBall,
    "key": Key,
    "antidoticCharm": AntidoticCharm,
    "antidoteBottle": AntidoteBottle,
    "vampiricFang": VampiricFang,
    "bulwarkCharm": BulwarkCharm,
    "berserkerBand": BerserkerBand,
    "glassIdol": GlassIdol,
    "scavengerPurse": ScavengerPurse,
    "phoenixFeather": PhoenixFeather,
    "venomRing": VenomRing,
    "regenBand": RegenBand,
    "energyCrystal": EnergyCrystal,
    "zombieCrown": ZombieCrown,
}


def from_json(j: dict[str, Any]) -> Any:
    type: str = j["item_type"]
    _class: type[Item] = item_type_to_class.get(j["item_type"], Item)
    return _class.from_json(j)


RELIC_POOL = [
    ManaBooster,
    ThornedAmulet,
    QuickBoots,
    AntidoticCharm,
    VampiricFang,
    BulwarkCharm,
    BerserkerBand,
    GlassIdol,
    ScavengerPurse,
    PhoenixFeather,
    VenomRing,
    RegenBand,
    EnergyCrystal,
]
