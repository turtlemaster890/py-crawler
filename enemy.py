from typing import TypedDict, TYPE_CHECKING
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
    ):
        self.enemy_type = enemy_type or "goblin"
        self.name = name or "Enemy"
        self.combatHandler = handler
        with open(getRelativePath("enemy_stats.json"), "r") as f:
            all_stats: dict[str, EnemyStats] = json.load(f)
            self.stats = all_stats[self.enemy_type]

        self.max_health: int = self.stats["health"]
        self.speed: int = self.stats["speed"]
        self.health = self.max_health
        self.action = ""
        self.aggro = []

    def combatStart(self, handler: CombatHandler):
        self.combatHandler = handler
        self.aggro = [[0, player] for player in self.combatHandler.players]
        self.decideAction()

    def decideAction(self):
        actList = []
        for actName, act in self.stats["actions"].items():
            actList.extend([actName] * act["weight"])
        if actList == []:
            actList = ["pass"]
        self.action = random.choice(actList)

    def to_json(self):
        return {
            "enemy_type": self.enemy_type,
            "name": self.name,
            "max_health": self.max_health,
            "speed": self.speed,
            "health": self.health,
        }

    @classmethod
    def from_json(cls, j):
        new_enemy = cls(j["name"])
        new_enemy.max_health = j["max_health"]
        new_enemy.speed = j["speed"]
        new_enemy.health = j["health"]
        return new_enemy

    def turnStart(self, handler: CombatHandler):
        for player in self.aggro:
            player[0] /= 2
        self.takeAction(self.action, handler)
        utils.wait_for_enter()
        self.decideAction()

    def takeAction(self, action: str, handler: CombatHandler):
        action_method = getattr(self, action, None)
        if action_method:
            action_method(handler)
        utils.wait_for_enter()

    def attack(self, handler: CombatHandler):
        target = min(self.aggro, key=lambda x: x[0])[1]
        target.takeDamage(handler, self.stats["actions"]["attack"]["damage"], self)
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} attacks {target.name} for {self.stats["actions"]["attack"]["damage"]} damage."
        )

    def takeDamage(self, handler: CombatHandler, damage: int, attacker=None):
        for player in self.aggro:
            if player[1] is attacker:
                player[0] += damage
        self.health -= damage
        if self.health <= 0:
            self.die(handler)

    def heal(self, amount: int):
        self.health = min(self.max_health, self.health + amount)

    def die(self, handler: CombatHandler):
        handler.removeEnemy(self)
        terminalDisplay.updateDisplays()
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} has been defeated!")
        utils.wait_for_enter()


class Goblin(enemy):
    def __init__(self, name: str = "Goblin"):
        super().__init__(name, "goblin")

    def rob(self, handler: CombatHandler):
        stolen = random.randint(3, 7)
        terminalDisplay.updateDisplays()
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} steals {stolen} from you!"
        )
        handler.party.funds -= min(stolen, handler.party.funds)


class Skeleton(enemy):
    def __init__(self, name: str = "Skeleton"):
        super().__init__(name, "skeleton")


class SmallSlime(enemy):
    def __init__(self, name: str = "Small Slime"):
        super().__init__(name, "small_slime")


class LargeSlime(enemy):
    def __init__(self, name: str = "Large Slime"):
        super().__init__(name, "large_slime")

    def turnStart(self, handler: CombatHandler):
        if self.health <= self.max_health / 2:
            self.takeAction("split", handler)
        else:
            self.decideAction()
            self.takeAction(self.action, handler)

    def split(self, handler: CombatHandler):
        handler.addEnemy(SmallSlime())
        handler.addEnemy(SmallSlime())
        handler.removeEnemy(self)
        terminalDisplay.updateDisplays()
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} splits into two!")


class Necromancer(enemy):
    def __init__(self, name: str = "Necromancer"):
        super().__init__(name, "necromancer")

    def raise_undead(self, handler: CombatHandler):
        handler.addEnemy(Skeleton())
        handler.addEnemy(Skeleton())


class NormalGuy(enemy):
    def __init__(self, name: str = "Normal Guy"):
        super().__init__(name, "normal_guy")

    def die(self, handler: CombatHandler):
        handler.removeEnemy(self)
        terminalDisplay.updateDisplays()
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} has been defeated!")
        utils.wait_for_enter()
        terminalDisplay.contextDisplay.print_boxify(
            f"Wait... {self.name} gets back up!"
        )
        utils.wait_for_enter()
        handler.addEnemy(Werewolf(f"Werewolf ({self.name})"))

    def greet(self, handler: CombatHandler):
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} says hello.")
        utils.wait_for_enter()

    def handshake(self, handler: CombatHandler):
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} shakes your hand.")
        utils.wait_for_enter()


class Werewolf(enemy):
    def __init__(self, name: str = "Werewolf"):
        super().__init__(name, "werewolf")

    def howl(self, handler: CombatHandler):
        handler.addEnemy(Werewolf())


enemy_type_to_class = {
    "goblin": Goblin,
    "skeleton": Skeleton,
    "small_slime": SmallSlime,
    "large_slime": LargeSlime,
    "necromancer": Necromancer,
    "normal_guy": NormalGuy,
    "werewolf": Werewolf,
}


def from_json(j: dict[str, object]):
    _class = enemy_type_to_class.get(j["enemy_type"], enemy)  # type: ignore
    return _class.from_json(j)
