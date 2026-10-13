from typing import TypedDict, Literal, Any, TYPE_CHECKING, Callable
import json
import random
import terminalDisplay
from utils import getRelativePath
from turnEntry import TurnEntry
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
    def __init__(self, name: str = "Enemy", enemy_type: str = "goblin", handler: CombatHandler | None = None):
        self.enemy_type = enemy_type or "goblin"
        self.name = name or "Enemy"
        self.combat = handler
        with open(getRelativePath("enemy_stats.json"), "r") as f:
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

    def to_json(self):
        return {
            'enemy_type': self.enemy_type,
            'name': self.name,
            'max_health': self.max_health,
            'speed': self.speed,
            'health': self.health
        }

    @classmethod
    def from_json(cls, j):
        new_enemy = cls(j['name'])
        new_enemy.max_health = j['max_health']
        new_enemy.speed = j['speed']
        new_enemy.health = j['health']
        return new_enemy



    def turnStart(self, handler: CombatHandler):
        self.decideAction()
        self.takeAction(self.action, handler)
        utils.wait_for_enter()

    def takeAction(self, action: str, handler: CombatHandler):
        action_method = getattr(self, action, None)
        if action_method:
            action_method(handler)

    def attack(self, handler: CombatHandler):
        random.choice(handler.players).health -= self.stats["actions"]["attack"]["damage"]

    def takeDamage(self, handler: CombatHandler, damage: int):
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
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} steals {stolen} from you!")
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
        utils.wait_for_enter()

enemy_type_to_class = {
    'goblin': Goblin,
    'skeleton': Skeleton,
    'small_slime': SmallSlime,
    'large_slime': LargeSlime
}

def from_json(j: dict[str, object]):
    _class = enemy_type_to_class.get(j['enemy_type'], enemy) #type: ignore
    return _class.from_json(j)