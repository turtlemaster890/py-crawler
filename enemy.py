from dataclasses import dataclass
from typing import Any, Self, Sequence, TypedDict, TYPE_CHECKING
import json
import random
from conditions import (
    Burning,
    Condition,
    ConditionReturnActions,
    Rotten,
    applyDamageHooks,
    inflict,
)
from combatHandler import CombatHandler
from item import (
    RELIC_POOL,
    Bone,
    HealthPotion,
    Item,
    Relic,
    RustyCoin,
    ZombieCrown,
)
import terminalDisplay
from utils import getRelativePath

if TYPE_CHECKING:
    from combatHandler import CombatHandler
    from player import Player


class ActionInfo(TypedDict):
    weight: int
    damage: int


@dataclass
class AggroEntry:
    value: int
    player: Player


class EnemyStats(TypedDict):
    speed: int
    health: int
    actions: dict[str, ActionInfo]


class Enemy:
    def __init__(
        self,
        name: str = "Enemy",
        enemy_type: str = "goblin",
        handler: CombatHandler | None = None,
    ) -> None:
        self.damage_mult: float = 1.0
        self.enemy_type: str = enemy_type or "goblin"
        self.name: str = name or "Enemy"
        self.combatHandler: CombatHandler | None = handler
        self.conditions: list[Condition] = []
        with open(getRelativePath("enemy_stats.json"), "r") as f:
            all_stats: dict[str, EnemyStats] = json.load(f)
            self.stats: EnemyStats = all_stats[self.enemy_type]

        self.max_health: int = self.stats["health"]
        self.speed: int = self.stats["speed"]
        self.health: int = self.max_health
        self.action: str = ""
        self.aggro: list[AggroEntry] = []
        self.loot_table: list[tuple[int, Sequence[Item]]] = [(1, [])]

    def scale(self, floor: int) -> None:
        f = floor - 1
        self.max_health = round(self.max_health * (1 + 0.25 * f))
        self.health = self.max_health
        self.damage_mult = 1 + 0.15 * f

    def combatStart(self, handler: CombatHandler) -> None:
        self.combatHandler = handler
        self.aggro = [
            AggroEntry(value=0, player=player) for player in self.combatHandler.players
        ]
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
            "damage_mult": self.damage_mult,
        }

    @classmethod
    def from_json(cls, j) -> Self:
        new_enemy: Self = cls(j["name"])
        new_enemy.max_health = j["max_health"]
        new_enemy.speed = j["speed"]
        new_enemy.health = j["health"]
        new_enemy.damage_mult = j.get("damage_mult", 1.0)
        return new_enemy

    def turnStart(self, handler: CombatHandler) -> None:
        if self.tickConditions():
            terminalDisplay.contextDisplay.print_boxify(
                f"{self.name} stands still, seemingly frozen."
            )
            handler.pause()
            return
        self.aggro = [entry for entry in self.aggro if entry.player in handler.players]
        for player in self.aggro:
            player.value //= 2
        self.takeAction(self.action, handler)
        self.decideAction()

    def tickConditions(self) -> bool:
        skip_turn = False
        for cond in self.conditions[:]:
            if cond.turnStart() == ConditionReturnActions.SKIP_TURN:
                skip_turn = True
        return skip_turn

    def inspect(self, handler: CombatHandler):
        text = f"Health: {self.health}/{self.max_health}"
        if self.conditions:
            text += f" Conditions: {', '.join(c.name for c in self.conditions)}"
        terminalDisplay.say(text)
        handler.pause()

    def takeAction(self, action: str, handler: CombatHandler) -> None:
        action_method: Any | None = getattr(self, action, None)
        if action_method:
            action_method(handler)
        else:
            info = self.stats["actions"].get(action, {})
            if "inflict" in info:
                self.inflictAction(info, handler)
        handler.pause()

    def attack(self, handler: CombatHandler) -> None:
        target: Player = random.choice(
            [
                entry.player
                for entry in self.aggro
                if entry == max(self.aggro, key=lambda x: x.value)
            ]
        )
        target.takeDamage(handler, self.stats["actions"]["attack"]["damage"], self)
        handler.announce(
            f"{self.name} attacks {target.name} for {self.stats["actions"]["attack"]["damage"]} damage."
        )
        spec = self.stats["actions"]["attack"].get("inflict")
        if spec:
            handler.pause()
            self.applyInflict(spec, target, handler)

    def takeDamage(
        self,
        handler: CombatHandler,
        damage: int,
        attacker: Player | None = None,
        damage_type: str = "",
    ) -> None:
        damage = applyDamageHooks(damage, attacker, self, damage_type)
        for player in self.aggro:
            if player.player is attacker:
                player.value += damage
        self.health -= damage
        if self.health <= 0:
            self.die(handler)

    def heal(self, amount: int) -> None:
        self.health: int = min(self.max_health, self.health + amount)

    def die(self, handler: CombatHandler) -> None:
        for p in handler.players:
            for r in p.inventory.items:
                if isinstance(r, Relic):
                    r.enemyDeath(self)
        handler.removeEnemy(self)
        handler.refresh()
        handler.announce(f"{self.name} has been defeated!")
        handler.pause()
        drops: Sequence[Item] = random.choices(
            [l[1] for l in self.loot_table], [l[0] for l in self.loot_table], k=1
        )[0]
        if drops:
            terminalDisplay.contextDisplay.print_boxify(
                f"{self.name} drops {", ".join([i.name for i in drops])}"
            )
            for i in drops:
                handler.party.inventory.add(i)
            handler.pause()

    def applyCondition(self, condition: Condition, handler: CombatHandler) -> None:
        self.conditions.append(condition)
        condition.onApply()

    def applyInflict(
        self, spec: dict, target: Player | Enemy, handler: CombatHandler
    ) -> None:
        if target.health <= 0:
            return
        cond = inflict(spec, target, handler)
        if cond:
            terminalDisplay.contextDisplay.print_boxify(
                f"{target.name} is suddenly hit with {cond.name}!"
            )

    def inflictAction(self, info: dict, handler: CombatHandler) -> None:
        if info.get("text"):
            terminalDisplay.contextDisplay.print_boxify(
                info["text"].format(enemy=self.name)
            )
        targets = (
            handler.players[:]
            if info.get("target") == "all"
            else [random.choice(handler.players)]
        )
        for t in targets:
            self.applyInflict(info["inflict"], t, handler)


class Goblin(Enemy):
    def __init__(self, name: str = "Goblin") -> None:
        super().__init__(name, "goblin")
        self.loot_table = [(1, [RustyCoin()]), (1, [])]

    def rob(self, handler: CombatHandler) -> None:
        stolen: int = min(random.randint(3, 7), handler.party.funds)
        handler.refresh()
        handler.announce(f"{self.name} steals {stolen} from you!")
        handler.party.funds -= min(stolen, handler.party.funds)


class Skeleton(Enemy):
    def __init__(self, name: str = "Skeleton") -> None:
        super().__init__(name, "skeleton")
        self.loot_table = [(1, [Bone()])]


class SmallSlime(Enemy):
    def __init__(self, name: str = "Small Slime") -> None:
        super().__init__(name, "small_slime")


class LargeSlime(Enemy):
    def __init__(self, name: str = "Large Slime") -> None:
        super().__init__(name, "large_slime")

    def turnStart(self, handler: CombatHandler) -> None:
        if self.tickConditions():
            return
        if self.health <= self.max_health / 2:
            self.takeAction("split", handler)
        else:
            self.decideAction()
            self.takeAction(self.action, handler)

    def split(self, handler: CombatHandler) -> None:
        handler.addEnemy(SmallSlime())
        handler.addEnemy(SmallSlime())
        handler.removeEnemy(self)
        handler.refresh()
        handler.announce(f"{self.name} splits into two!")


class Necromancer(Enemy):
    def __init__(self, name: str = "Necromancer") -> None:
        super().__init__(name, "necromancer")

    def raise_undead(self, handler: CombatHandler) -> None:
        handler.announce(
            f"{self.name} brings their hand up. Skeletons emerge from the ground.", True
        )
        handler.addEnemy(Skeleton())
        handler.addEnemy(Skeleton())


class NormalGuy(Enemy):
    def __init__(self, name: str = "Normal Guy") -> None:
        super().__init__(name, "normal_guy")

    def die(self, handler: CombatHandler) -> None:
        handler.removeEnemy(self)
        handler.refresh()
        handler.announce(f"{self.name} has been defeated!")
        handler.pause()
        handler.announce(f"Wait... {self.name} gets back up!", True)
        handler.pause()
        handler.addEnemy(Werewolf(f"{self.name} (Wolf)"))

    def greet(self, handler: CombatHandler) -> None:
        handler.announce(f"{self.name} says hello.")

    def handshake(self, handler: CombatHandler) -> None:
        handler.announce(f"{self.name} shakes your hand.")


class Werewolf(Enemy):
    def __init__(self, name: str = "Werewolf") -> None:
        super().__init__(name, "werewolf")

    def howl(self, handler: CombatHandler) -> None:
        handler.announce(f"{self.name} howls at the moon...", True)
        handler.addEnemy(Wolf())


class Wolf(Enemy):
    def __init__(self, name: str = "Wolf") -> None:
        super().__init__(name, "wolf")


class Jelly(Enemy):
    def __init__(self, name: str = "Jelly") -> None:
        super().__init__(name, "jelly")

    def split(self, handler: CombatHandler) -> None:
        handler.announce(f"{self.name} splits")
        handler.removeEnemy(self)
        handler.addEnemy(BabyJelly())
        handler.addEnemy(BabyJelly())
        handler.addEnemy(BabyJelly())


class BabyJelly(Enemy):
    def __init__(self, name: str = "Baby Jelly") -> None:
        super().__init__(name, "baby_jelly")
        self.growth = 0

    def grow(self, handler: CombatHandler) -> None:
        self.growth += 1
        if self.growth >= 3:
            handler.announce(f"{self.name} suddenly grows larger.")
            handler.removeEnemy(self)
            handler.addEnemy(Jelly())
        else:
            handler.announce(f"{self.name} sits there.")


class StoneTitan(Enemy):
    def __init__(self, name: str = "Stone Titan") -> None:
        super().__init__(name, "stone_titan")
        self.coreCharge = 0
        self.bursts = 0
        self.enraged = False

    def to_json(self):
        j = super().to_json()
        j.update(core_charge=self.coreCharge, bursts=self.bursts, enraged=self.enraged)
        return j

    @classmethod
    def from_json(cls, j) -> Self:
        t = super().from_json(j)
        t.coreCharge = j.get("core_charge", 0)
        t.bursts = j.get("bursts", 0)
        t.enraged = j.get("enraged", 0)
        return t

    def attack(self, handler: CombatHandler) -> None:
        target: Player = random.choice(
            [
                entry.player
                for entry in self.aggro
                if entry == max(self.aggro, key=lambda x: x.value)
            ]
        )
        damage: int = self.stats["actions"]["attack"]["damage"] + (5 * self.bursts)
        target.takeDamage(handler, damage, self)
        handler.announce(f"{self.name} attacks {target.name} for {damage} damage.")

    def turnStart(self, handler: CombatHandler) -> None:
        if self.tickConditions():
            return
        if not self.enraged and self.health <= self.max_health / 2:
            self.enrage(handler)
        if self.coreCharge >= 5:
            self.takeAction("core_burst", handler)
            self.decideAction()
        else:
            super().turnStart(handler)

    def enrage(self, handler: CombatHandler) -> None:
        self.enraged = True
        self.speed += 30
        self.coreCharge = max(self.coreCharge, 3)
        terminalDisplay.contextDisplay.print_boxify(
            f"Cracks spread across {self.name}. Its core beings to pulse faster."
        )
        handler.pause()

    def slam(self, handler: CombatHandler) -> None:
        for player in handler.players[:]:
            player.takeDamage(handler, 5 + (2 * self.bursts), self)
        handler.announce(f"{self.name} slams the ground and a shockwave appears.")
        if self.enraged and handler.players:
            self.applyInflict(
                {"type": "stunned", "duration": 1, "chance": 0.5},
                random.choice(handler.players),
                handler,
            )

    def charge(self, handler: CombatHandler) -> None:
        self.coreCharge += 2 if self.enraged else 1
        handler.announce(f"{self.name}'s core glows.")

    def core_burst(self, handler: CombatHandler) -> None:
        self.coreCharge = 0
        self.bursts += 1
        handler.announce(
            f"{self.name} bursts into a glowing light. It seems... stronger now?"
        )

    def die(self, handler: CombatHandler) -> None:
        floor = handler.party.floor
        relics: list[type[Relic]] = RELIC_POOL
        picks = random.sample(relics, k=min(len(relics), 1 + floor // 3))
        self.loot_table = [
            (1, [r() for r in picks] + [HealthPotion() for _ in range(floor)])
        ]
        super().die(handler)
        reward = 500 * handler.party.floor
        handler.party.funds += reward
        terminalDisplay.contextDisplay.print_boxify(
            f"You find ¢{reward} in the rubble."
        )
        handler.pause()
        handler.victory = True


class ZombieKing(Enemy):
    def __init__(self, name: str = "Zombie King") -> None:
        super().__init__(name, "zombie_king")

    def reinforce(self, handler: CombatHandler) -> None:
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} raises their hand. Many enemies come from the ground, but they seem... off."
        )
        enemy_pool: list[type[Enemy]] = [Goblin, Skeleton, Wolf, Pyromaniac]
        for e in random.choices(enemy_pool, k=4):
            enemy = e()
            enemy.applyCondition(Rotten(1, enemy, handler), handler)
            handler.addEnemy(enemy)

    def die(self, handler: CombatHandler) -> None:
        floor = handler.party.floor
        self.loot_table = [(1, [ZombieCrown()])]
        super().die(handler)
        reward = 500 * handler.party.floor
        handler.party.funds += reward
        terminalDisplay.contextDisplay.print_boxify(
            f"You find ¢{reward} in {self.name}'s oversized shirt."
        )
        handler.pause()
        handler.victory = True


class Mimic(Enemy):
    def __init__(self, name: str = "Mimic") -> None:
        super().__init__(name, "mimic")

    def bite(self, handler: CombatHandler):
        target: Player = random.choice(
            [
                entry.player
                for entry in self.aggro
                if entry == min(self.aggro, key=lambda x: x.value)
            ]
        )
        target.takeDamage(handler, 3, self)
        handler.announce(f"{self.name} attacks {target.name} for 3 damage.")

        if random.randint(0, 2) == 2:
            handler.pause()

            coins = random.randint(0, 1) == 1
            if coins:
                spilled_coins = random.randint(30, 65)
                handler.announce(f"¢{spilled_coins} spills from {self.name}'s mouth!")
                handler.party.funds += spilled_coins
            else:
                it = RustyCoin()
                target.inventory.add(it)
                handler.announce(
                    f"{self.name} drops a {it.name}. {target.name} picks it up."
                )


class Pyromaniac(Enemy):
    def __init__(self, name: str = "Pyromaniac") -> None:
        super().__init__(name, "pyromaniac")

    def molotov(self, handler: CombatHandler):
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} throws a glass bottle. Flames rise up in the room."
        )
        for p in handler.players:
            p.applyCondition(Burning(3, p, handler), handler)


enemy_type_to_class = {
    "goblin": Goblin,
    "skeleton": Skeleton,
    "small_slime": SmallSlime,
    "large_slime": LargeSlime,
    "necromancer": Necromancer,
    "normal_guy": NormalGuy,
    "werewolf": Werewolf,
    "wolf": Wolf,
    "jelly": Jelly,
    "baby_jelly": BabyJelly,
    "stone_titan": StoneTitan,
    "mimic": Mimic,
    "pyromaniac": Pyromaniac,
    "zombie_king": ZombieKing,
}


def from_json(j: dict[str, object]):
    _class = enemy_type_to_class.get(j["enemy_type"], Enemy)  # type: ignore
    return _class.from_json(j)
