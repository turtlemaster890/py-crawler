from dataclasses import replace
import json
from enemy import Enemy
import inventory
from item import Item, Weapon, Armor, Relic
import menuHelper
import playerClass
import terminalDisplay
from actions import CombatActionEntry, PlayerAction
from conditions import Condition, ConditionReturnActions, applyDamageHooks
from utils import getRelativePath
from typing import TYPE_CHECKING, Self, TypedDict

import utils

if TYPE_CHECKING:
    from party import Party
    from combatHandler import CombatHandler


class BaseStats(TypedDict):
    health: int
    speed: int
    stamina: int


class StartingItems(TypedDict):
    weapon: str
    armor: str
    items: list[str]


class PlayerStats(TypedDict):
    base_stats: BaseStats
    starting_items: StartingItems


class Player:
    def __init__(self, name: str = "Player", class_type: str = "warrior") -> None:
        self.name: str = name
        self.class_type: str = class_type
        self.player_class = playerClass.classFromStr(class_type)
        self.inventory = inventory.PlayerInventory()

        with open(getRelativePath("player_stats.json"), "r") as f:
            all_stats: dict[str, PlayerStats] = json.load(f)
            self.stats: PlayerStats = all_stats[self.class_type]

        self.combat: CombatHandler | None = None
        self.speed: int = self.stats["base_stats"]["speed"]
        self.max_health: int = self.stats["base_stats"]["health"]
        self.health: int = self.max_health
        self.max_stamina: int = self.stats["base_stats"]["stamina"]
        self.stamina: int = self.max_stamina
        self.conditions: list[Condition] = []
        self.inventory.equip(Weapon(self.stats["starting_items"]["weapon"]))
        self.inventory.equip(Armor(self.stats["starting_items"]["armor"]))
        for item in self.stats["starting_items"]["items"]:
            self.inventory.add(Item(item))

    def to_json(self):
        return {
            "name": self.name,
            "class_type": self.class_type,
            "inventory": self.inventory.to_json(),
            "speed": self.speed,
            "max_health": self.max_health,
            "health": self.health,
            "max_stamina": self.max_stamina,
            "stamina": self.stamina,
        }

    @classmethod
    def from_json(cls, j) -> Self:
        new_player: Self = cls(name=j["name"], class_type=j["class_type"])
        new_player.inventory = inventory.from_json(j["inventory"])
        new_player.speed = j["speed"]
        new_player.max_health = j["max_health"]
        new_player.health = j["health"]
        new_player.max_stamina = j["max_stamina"]
        new_player.stamina = j["stamina"]
        return new_player

    def inspect(self, handler: CombatHandler):
        text = f"Health: {self.health}/{self.max_health} Stamina: {self.stamina}/{self.max_stamina}"
        if self.conditions:
            text += f" Conditions: {", ".join([cond.name for cond in self.conditions])}"
        terminalDisplay.say(text)
        handler.pause()

    def getTurnOptions(self, handler: CombatHandler) -> list[CombatActionEntry]:
        actions: list[CombatActionEntry] = [
            CombatActionEntry("Attack", self.attack),
            CombatActionEntry("Pass", lambda p, h: True),
            # (
            #     "kill other player",
            #     lambda h: h.select_character(
            #         lambda c: isinstance(c, Player) and not c is self
            #     )[0].takeDamage(h, 1000),
            #     "Hehe silly",
            # ),
            CombatActionEntry(
                "Scorching Ray", self.scorching_ray, "Multi-target magic beam", 10
            ),
            CombatActionEntry(
                "Inspect",
                lambda p, h: h.select_character(p, lambda c: True)[0].inspect(h),
                "Inspect Entry.",
            ),
        ]
        for it, n in inventory.group_items(self.inventory.items):
            for a in it.combat_actions:
                actions.append(replace(a, name=f"{a.name} (x{n})") if n > 1 else a)
        if self.inventory.weapon:
            actions.extend(self.inventory.weapon.combat_actions)
        if self.inventory.armor:
            actions.extend(self.inventory.armor.combat_actions)
        actions.extend(self.player_class.combat_actions)
        if utils.DEBUG_WIN_ACTION:
            actions.append(
                CombatActionEntry(
                    "debug.win",
                    lambda p, h: [
                        [c.takeDamage(h, 1000, p) for c in h.enemies.copy()],
                        True,
                    ][1],
                    "Win.",
                )
            )
        return [action for action in actions if action.stamina_cost <= self.stamina]

    def action_menu(self, party: Party) -> None:
        actions: list[tuple[str, PlayerAction]] = [
            ("View Inventory", self.inventory_menu)
        ]
        actions.extend(self.player_class.player_actions)

        # for i in self.inventory.items:
        #     actions.extend(i.player_actions)
        while True:
            option: int = menuHelper.menu("Actions", [ac[0] for ac in actions])
            if option != -1:
                actions[option][1](party, self)
            else:
                return

    def attack(self, player: Player, handler: CombatHandler) -> bool:
        if not self.inventory.weapon:
            return False
        to_attack: Player | Enemy = handler.select_character(
            self, lambda c: not isinstance(c, Player)
        )[0]
        damage: int = self.inventory.weapon.damage
        damage = self.relicDamage(damage, to_attack)
        to_attack.takeDamage(handler, damage, self)
        return True

    def takeDamage(
        self, handler: CombatHandler, damage: int, attacker=None, damage_type: str = ""
    ) -> None:
        damage = applyDamageHooks(damage, attacker, self, damage_type)
        for relic in self.inventory.items:
            if isinstance(relic, Relic):
                r = relic.takeDamage(damage, attacker, self, damage_type)
                if r is not None:
                    damage = r
        if self.inventory.armor and damage > 0:
            damage = max(1, damage - self.inventory.armor.defense)
        self.health -= damage
        if self.health <= 0:
            self.die(handler)

    def die(self, handler: CombatHandler):
        handler.announce(f"Player {self.name} dies!")
        for relic in self.inventory.items[:]:
            if isinstance(relic, Relic):
                relic.die()
        if self.health > 0:
            return
        print(f"Player {self.name} dies!")
        for condition in self.conditions[:]:
            condition.die()
        handler.removePlayer(self)

    def applyCondition(self, condition: Condition, handler: CombatHandler) -> None:
        self.conditions.append(condition)
        condition.onApply()

    def has_condition(self, condition: type[Condition]) -> Condition | None:
        for cond in self.conditions:
            if isinstance(cond, condition):
                return cond

    def relicDamage(
        self, damage: int, target: Player | Enemy, damage_type: str = ""
    ) -> int:
        for item in self.inventory.items:
            if isinstance(item, Relic):
                r = item.dealDamage(damage, self, target, damage_type)
                if r is not None:
                    damage = r
        return damage

    def pretty_print_turn_options(
        self,
        options: list[CombatActionEntry],
        selected: int,
        w: int,
        h: int,
    ) -> list[str]:
        content_width: int = w - 2
        content_height: int = h - 2
        out: list[str] = []
        out.append("┌" + "─" * content_width + "┐")
        for i in range(min(content_height, len(options))):
            opt: CombatActionEntry = options[i]
            out.append(
                "│"
                + (("> " if i == selected else "  ") + opt.name).ljust(content_width)
                + "│"
            )
        out.append("└" + "─" * content_width + "┘")
        return out

    def turnStart(self, handler: CombatHandler) -> None:
        self.stamina: int = min(self.max_stamina, self.stamina + 1)
        skip_turn = False
        for condition in self.conditions[:]:
            if condition.turnStart() == ConditionReturnActions.SKIP_TURN:
                skip_turn = True
        if skip_turn:
            terminalDisplay.contextDisplay.print_boxify(
                f"{self.name} stands still, seemingly frozen."
            )
            handler.pause()
            return
        for relic in self.inventory.items:
            if isinstance(relic, Relic):
                relic.turnStart()

        while True:
            op: list[CombatActionEntry] = self.getTurnOptions(handler)
            index = handler.choose_action(self, op)
            self.stamina -= op[index].stamina_cost
            if op[index].action(self, handler):
                return

    def moveItemToParty(self, party: Party, item: Item) -> bool:
        if item not in self.inventory:
            return False
        if not self.inventory.remove(item):
            return False
        if not party.inventory.add(item):
            self.inventory.add(item)
            return False
        return True

    def inventory_menu(self, party: Party, _) -> None:
        while True:
            groups = inventory.group_items(self.inventory.items)
            option: int = menuHelper.menu(
                "Pick an item", [inventory.stack_label(i, n) for i, n in groups]
            )
            if option == -1:
                return
            it: Item = groups[option][0]
            action_options: list[tuple[str, PlayerAction]] = [
                (
                    "Move to party",
                    lambda party, player: self.moveItemToParty(party, it),
                )
            ]
            action_options.extend(it.player_actions)
            act_options_strs: list[str] = [ac[0] for ac in action_options]
            while True:
                act: int = menuHelper.menu("Action to take:", act_options_strs)
                if act == -1:
                    break
                if action_options[option][1](party, self):
                    return

    def startCombat(self, handler: CombatHandler) -> None:
        for relic in self.inventory.items:
            if isinstance(relic, Relic):
                relic.player = self
                relic.combatStart(handler)

    def leaveCombat(self) -> None:
        for c in self.conditions[:]:
            c.changeDuration(-c.duration)
        for r in self.inventory.items:
            if isinstance(r, Relic):
                r.combatEnd()

    def scorching_ray(self, player: Player, handler: CombatHandler):
        to_attack: list[Player | Enemy] = handler.select_character(
            self, lambda c: not isinstance(c, Player), 3, 1
        )
        for c in to_attack:
            damage: int = 5
            damage = self.relicDamage(damage, c, "magic")
            c.takeDamage(handler, damage, self)
        return True

    def modifyOutgoing(
        self, damage: int, target: Player | Enemy, damage_type: str = ""
    ):
        for src in [
            i for i in self.inventory.items if isinstance(i, Relic)
        ] + self.conditions:
            r = src.dealDamage(damage, self, target, damage_type)
            if r is not None:
                damage = r
        return max(0, damage)
