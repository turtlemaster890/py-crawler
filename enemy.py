from typing import TypedDict, Literal, Any, TYPE_CHECKING, Callable
import json
import random
from turnEntry import TurnEntry
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
    def __init__(self, name: str = "Enemy", enemy_type: str = "goblin"):
        self.enemy_type = enemy_type or "goblin"
        self.name = name or "Enemy"
        with open("enemy_stats.json", "r") as f:
            all_stats: dict[str, EnemyStats] = json.load(f)
            self.stats = all_stats[self.enemy_type]
            
        self.max_health: int = self.stats["health"]
        self.speed: int = self.stats["speed"]
        self.health = self.max_health
        self.action = ""

    def decideAction(self):
        actList = []
        for actName, act in self.stats["actions"].items():
            actList.extend([actName] * act["weight"])
        if actList == []:
            actList = ["pass"]
        self.action = random.choice(actList)


    def turnStart(self, handler: CombatHandler):
        self.decideAction()
        self.takeAction(self.action, handler)
        input()

    def takeAction(self, action: str, handler: CombatHandler):
        action_method = getattr(self, action, None)
        if action_method:
            action_method(handler)

    def attack(self, handler: CombatHandler):
        random.choice(handler.players).health -= self.stats["actions"]["attack"]["damage"]

class Goblin(enemy):
    def __init__(self, name: str = "Goblin"):
        super().__init__(name, "goblin")
    def rob(self, handler: CombatHandler):
        stolen = random.randint(3, 7)
        print(f"{self.name} steals {stolen} from you!")
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
            self.takeAction(self.action, handler)
    def split(self, handler: CombatHandler):
        handler.addEnemy(SmallSlime())
        handler.addEnemy(SmallSlime())
        handler.removeEnemy(self)