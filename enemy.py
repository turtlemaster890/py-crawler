from typing import Any, Self, TypedDict, TYPE_CHECKING
import json
import random
from combatHandler import CombatHandler
import terminalDisplay
from utils import getRelativePath
import utils

if TYPE_CHECKING:
    from combatHandler import CombatHandler


class ActionInfo(TypedDict):
    weight: int
    damage: int


class EnemyStats(TypedDict):
    speed: int
    health: int
    actions: dict[str, ActionInfo]


class enemy:
    def __init__(
        self,
        name: str = "Enemy",
        enemy_type: str = "goblin",
        handler: CombatHandler | None = None,
    ) -> None:
        self.enemy_type: str = enemy_type or "goblin"
        self.name: str = name or "Enemy"
        self.combatHandler: CombatHandler | None = handler
        with open(getRelativePath("enemy_stats.json"), "r") as f:
            all_stats: dict[str, EnemyStats] = json.load(f)
            self.stats: EnemyStats = all_stats[self.enemy_type]

        self.max_health: int = self.stats["health"]
        self.speed: int = self.stats["speed"]
        self.health: int = self.max_health
        self.action: str = ""
        self.aggro = []

    def combatStart(self, handler: CombatHandler) -> None:
        self.combatHandler = handler
        self.aggro = [[0, player] for player in self.combatHandler.players]
        self.decideAction()

    def decideAction(self) -> None:
        actList = []
        for actName, act in self.stats["actions"].items():
            actList.extend([actName] * act["weight"])
        if actList == []:
            actList: list[str] = ["pass"]
        self.action: str = random.choice(actList)

    def to_json(self):
        return {
            "enemy_type": self.enemy_type,
            "name": self.name,
            "max_health": self.max_health,
            "speed": self.speed,
            "health": self.health,
        }

    @classmethod
    def from_json(cls, j) -> Self:
        new_enemy: Self = cls(j["name"])
        new_enemy.max_health = j["max_health"]
        new_enemy.speed = j["speed"]
        new_enemy.health = j["health"]
        return new_enemy

    def turnStart(self, handler: CombatHandler) -> None:
        self.aggro = [entry for entry in self.aggro if entry[1] in handler.players]
        for player in self.aggro:
            player[0] /= 2
        self.takeAction(self.action, handler)
        self.decideAction()

    def takeAction(self, action: str, handler: CombatHandler) -> None:
        action_method: Any | None = getattr(self, action, None)
        if action_method:
            action_method(handler)
        utils.wait_for_enter()

    def attack(self, handler: CombatHandler) -> None:
        target = random.choice(
            [
                entry[1]
                for entry in self.aggro
                if entry == min(self.aggro, key=lambda x: x[0])
            ]
        )
        target.takeDamage(handler, self.stats["actions"]["attack"]["damage"], self)
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} attacks {target.name} for {self.stats["actions"]["attack"]["damage"]} damage."
        )

    def takeDamage(self, handler: CombatHandler, damage: int, attacker=None) -> None:
        for player in self.aggro:
            if player[1] is attacker:
                player[0] += damage
        self.health -= damage
        if self.health <= 0:
            self.die(handler)

    def heal(self, amount: int) -> None:
        self.health: int = min(self.max_health, self.health + amount)

    def die(self, handler: CombatHandler) -> None:
        handler.removeEnemy(self)
        terminalDisplay.updateDisplays()
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} has been defeated!")
        utils.wait_for_enter()


class Goblin(enemy):
    def __init__(self, name: str = "Goblin") -> None:
        super().__init__(name, "goblin")

    def rob(self, handler: CombatHandler) -> None:
        stolen: int = random.randint(3, 7)
        terminalDisplay.updateDisplays()
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} steals {stolen} from you!"
        )
        handler.party.funds -= min(stolen, handler.party.funds)


class Skeleton(enemy):
    def __init__(self, name: str = "Skeleton") -> None:
        super().__init__(name, "skeleton")


class SmallSlime(enemy):
    def __init__(self, name: str = "Small Slime") -> None:
        super().__init__(name, "small_slime")


class LargeSlime(enemy):
    def __init__(self, name: str = "Large Slime") -> None:
        super().__init__(name, "large_slime")

    def turnStart(self, handler: CombatHandler) -> None:
        if self.health <= self.max_health / 2:
            self.takeAction("split", handler)
        else:
            self.decideAction()
            self.takeAction(self.action, handler)

    def split(self, handler: CombatHandler) -> None:
        handler.addEnemy(SmallSlime())
        handler.addEnemy(SmallSlime())
        handler.removeEnemy(self)
        terminalDisplay.updateDisplays()
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} splits into two!")


class Necromancer(enemy):
    def __init__(self, name: str = "Necromancer") -> None:
        super().__init__(name, "necromancer")

    def raise_undead(self, handler: CombatHandler) -> None:
        terminalDisplay.contextDisplay.type_print(
            f"{self.name} brings their hand up. Skeletons emerge from the ground."
        )
        handler.addEnemy(Skeleton())
        handler.addEnemy(Skeleton())


class NormalGuy(enemy):
    def __init__(self, name: str = "Normal Guy") -> None:
        super().__init__(name, "normal_guy")

    def die(self, handler: CombatHandler) -> None:
        handler.removeEnemy(self)
        terminalDisplay.updateDisplays()
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} has been defeated!")
        utils.wait_for_enter()
        terminalDisplay.contextDisplay.type_print(f"Wait... {self.name} gets back up!")
        utils.wait_for_enter()
        handler.addEnemy(Werewolf(f"{self.name} (Wolf)"))

    def greet(self, handler: CombatHandler) -> None:
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} says hello.")

    def handshake(self, handler: CombatHandler) -> None:
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} shakes your hand.")


class Werewolf(enemy):
    def __init__(self, name: str = "Werewolf") -> None:
        super().__init__(name, "werewolf")

    def howl(self, handler: CombatHandler) -> None:
        terminalDisplay.contextDisplay.type_print(f"{self.name} howls at the moon...")
        handler.addEnemy(Werewolf())


class Jelly(enemy):
    def __init__(self, name: str = "Jelly") -> None:
        super().__init__(name, "jelly")

    def split(self, handler: CombatHandler) -> None:
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} splits.")
        handler.removeEnemy(self)
        handler.addEnemy(BabyJelly())
        handler.addEnemy(BabyJelly())
        handler.addEnemy(BabyJelly())


class BabyJelly(enemy):
    def __init__(self, name: str = "Baby Jelly") -> None:
        super().__init__(name, "baby_jelly")
        self.growth = 0

    def grow(self, handler: CombatHandler) -> None:
        self.growth += 1
        if self.growth >= 3:
            terminalDisplay.contextDisplay.print_boxify(
                f"{self.name} suddenly grows larger."
            )
            handler.removeEnemy(self)
            handler.addEnemy(Jelly())
        else:
            terminalDisplay.contextDisplay.print_boxify(f"{self.name} sits there.")


class StoneTitan(enemy):
    def __init__(self, name: str = "Stone Titan") -> None:
        super().__init__(name, "stone_titan")
        self.coreCharge = 0
        self.bursts = 0

    def attack(self, handler: CombatHandler) -> None:
        target = random.choice(
            [
                entry[1]
                for entry in self.aggro
                if entry == min(self.aggro, key=lambda x: x[0])
            ]
        )
        damage: int = self.stats["actions"]["attack"]["damage"] + (5 * self.bursts)
        target.takeDamage(handler, damage, self)
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} attacks {target.name} for {damage} damage."
        )

    def turnStart(self, handler: CombatHandler) -> None:
        if self.coreCharge >= 5:
            self.takeAction("core_burst", handler)
            self.decideAction()
        else:
            super().turnStart(handler)

    def slam(self, handler: CombatHandler) -> None:
        for player in handler.players:
            player.takeDamage(handler, 5 + (2 * self.bursts), self)

        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} slams the ground and a shockwave appears."
        )

    def charge(self, handler: CombatHandler) -> None:
        self.coreCharge += 1
        terminalDisplay.contextDisplay.print_boxify(f"{self.name}'s core glows.")

    def core_burst(self, handler: CombatHandler) -> None:
        self.coreCharge = 0
        self.bursts += 1
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} bursts into a glowing light. It seems... stronger now?"
        )

class Mimic(enemy):
    def __init__(self, name: str = "Mimic") -> None:
        super().__init__(name, "mimic")

    def bite(self, handler: CombatHandler):
        target = random.choice(
            [
                entry[1]
                for entry in self.aggro
                if entry == min(self.aggro, key=lambda x: x[0])
            ]
        )
        target.takeDamage(handler, 3, self)
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} attacks {target.name} for 3 damage."
        )
        # if random.randint(0, 2) == 2:
        #     utils.wait_for_enter()
        #     spilled_coins = random.randint(30, 65)
        #     terminalDisplay.contextDisplay.print_boxify(f"¢{spilled_coins} spills from {self.name}'s mouth!")
            
        

enemy_type_to_class = {
    "goblin": Goblin,
    "skeleton": Skeleton,
    "small_slime": SmallSlime,
    "large_slime": LargeSlime,
    "necromancer": Necromancer,
    "normal_guy": NormalGuy,
    "werewolf": Werewolf,
    "jelly": Jelly,
    "baby_jelly": BabyJelly,
    "stone_titan": StoneTitan,
}


def from_json(j: dict[str, object]):
    _class = enemy_type_to_class.get(j["enemy_type"], enemy)  # type: ignore
    return _class.from_json(j)
