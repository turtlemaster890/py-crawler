from dataclasses import dataclass
from typing import Any, Self, TypedDict, TYPE_CHECKING
import json
import random
from conditions import (
    Burning,
    Condition,
    ConditionReturnActions,
    applyDamageHooks,
    inflict,
)
from combatHandler import CombatHandler
from item import Bone, Item, ManaBooster, QuickBoots, RustyCoin, ThornedAmulet
import terminalDisplay
from utils import getRelativePath
import utils

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
        self.loot_table: list[tuple[int, list[Item]]] = [(1, [])]

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
        }

    @classmethod
    def from_json(cls, j) -> Self:
        new_enemy: Self = cls(j["name"])
        new_enemy.max_health = j["max_health"]
        new_enemy.speed = j["speed"]
        new_enemy.health = j["health"]
        return new_enemy

    def turnStart(self, handler: CombatHandler) -> None:
        if self.tickConditions():
            terminalDisplay.contextDisplay.print_boxify(
                f"{self.name} stands still, seemingly frozen."
            )
            utils.wait_for_enter()
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

    def inspect(self):
        text = f"Health: {self.health}/{self.max_health}"
        if self.conditions:
            text += f" Conditions: {', '.join(c.name for c in self.conditions)}"
        terminalDisplay.contextDisplay.print_boxify(text)
        utils.wait_for_enter()

    def takeAction(self, action: str, handler: CombatHandler) -> None:
        action_method: Any | None = getattr(self, action, None)
        if action_method:
            action_method(handler)
        else:
            info = self.stats["actions"].get(action, {})
            if "inflict" in info:
                self.inflictAction(info, handler)
        utils.wait_for_enter()

    def attack(self, handler: CombatHandler) -> None:
        target: Player = random.choice(
            [
                entry.player
                for entry in self.aggro
                if entry == min(self.aggro, key=lambda x: x.value)
            ]
        )
        target.takeDamage(handler, self.stats["actions"]["attack"]["damage"], self)
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} attacks {target.name} for {self.stats["actions"]["attack"]["damage"]} damage."
        )
        spec = self.stats["actions"]["attack"].get("inflict")
        if spec:
            utils.wait_for_enter()
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
        handler.removeEnemy(self)
        terminalDisplay.updateDisplays()
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} has been defeated!")
        utils.wait_for_enter()
        drops: list[Item] = random.choices(
            [l[1] for l in self.loot_table], [l[0] for l in self.loot_table], k=1
        )[0]
        if drops:
            terminalDisplay.contextDisplay.print_boxify(
                f"{self.name} drops {", ".join([i.name for i in drops])}"
            )
            for i in drops:
                handler.party.inventory.add(i)
            utils.wait_for_enter()

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
                f"{target.name} if {cond.name}!"
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
        terminalDisplay.updateDisplays()
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} steals {stolen} from you!"
        )
        handler.party.funds -= stolen


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
        terminalDisplay.updateDisplays()
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} splits into two!")


class Necromancer(Enemy):
    def __init__(self, name: str = "Necromancer") -> None:
        super().__init__(name, "necromancer")

    def raise_undead(self, handler: CombatHandler) -> None:
        terminalDisplay.contextDisplay.type_print(
            f"{self.name} brings their hand up. Skeletons emerge from the ground."
        )
        handler.addEnemy(Skeleton())
        handler.addEnemy(Skeleton())


class NormalGuy(Enemy):
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


class Werewolf(Enemy):
    def __init__(self, name: str = "Werewolf") -> None:
        super().__init__(name, "werewolf")

    def howl(self, handler: CombatHandler) -> None:
        terminalDisplay.contextDisplay.type_print(f"{self.name} howls at the moon...")
        handler.addEnemy(Wolf())


class Wolf(Enemy):
    def __init__(self, name: str = "Wolf") -> None:
        super().__init__(name, "wolf")


class Jelly(Enemy):
    def __init__(self, name: str = "Jelly") -> None:
        super().__init__(name, "jelly")

    def split(self, handler: CombatHandler) -> None:
        terminalDisplay.contextDisplay.print_boxify(f"{self.name} splits.")
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
            terminalDisplay.contextDisplay.print_boxify(
                f"{self.name} suddenly grows larger."
            )
            handler.removeEnemy(self)
            handler.addEnemy(Jelly())
        else:
            terminalDisplay.contextDisplay.print_boxify(f"{self.name} sits there.")


class StoneTitan(Enemy):
    def __init__(self, name: str = "Stone Titan") -> None:
        super().__init__(name, "stone_titan")
        self.coreCharge = 0
        self.bursts = 0
        self.enraged = False
        self.loot_table = [
            (1, [ThornedAmulet()]),
            (1, [QuickBoots()]),
            (1, [ManaBooster()]),
        ]

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
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} attacks {target.name} for {damage} damage."
        )

    def turnStart(self, handler: CombatHandler) -> None:
        if self.tickConditions():
            return
        if not self.enraged and self.health >= self.max_health / 2:
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
        utils.wait_for_enter()

    def slam(self, handler: CombatHandler) -> None:
        for player in handler.players[:]:
            player.takeDamage(handler, 5 + (2 * self.bursts), self)

        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} slams the ground and a shockwave appears."
        )
        if self.enraged and handler.players:
            self.applyInflict(
                {"type": "stunned", "duration": 1, "chance": 0.5},
                random.choice(handler.players),
                handler,
            )

    def charge(self, handler: CombatHandler) -> None:
        self.coreCharge += 2 if self.enraged else 1
        terminalDisplay.contextDisplay.print_boxify(f"{self.name}'s core glows.")

    def core_burst(self, handler: CombatHandler) -> None:
        self.coreCharge = 0
        self.bursts += 1
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} bursts into a glowing light. It seems... stronger now?"
        )

    def die(self, handler: CombatHandler) -> None:
        super().die(handler)
        handler.party.funds += 500
        terminalDisplay.contextDisplay.print_boxify("You find ¢500 in the rubble.")
        utils.wait_for_enter()
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
        terminalDisplay.contextDisplay.print_boxify(
            f"{self.name} attacks {target.name} for 3 damage."
        )
        if random.randint(0, 2) == 2:
            utils.wait_for_enter()
            coins = random.randint(0, 1) == 1
            if coins:
                spilled_coins = random.randint(30, 65)
                terminalDisplay.contextDisplay.print_boxify(
                    f"¢{spilled_coins} spills from {self.name}'s mouth!"
                )
                handler.party.funds += spilled_coins
            else:
                it = RustyCoin()
                target.inventory.add(it)
                terminalDisplay.contextDisplay.print_boxify(
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
}


def from_json(j: dict[str, object]):
    _class = enemy_type_to_class.get(j["enemy_type"], Enemy)  # type: ignore
    return _class.from_json(j)
