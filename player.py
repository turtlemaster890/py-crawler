import json
from enemy import Enemy
import inventory
from item import Item, Weapon, Armor, Relic
import menuHelper
import terminalDisplay
import inputController
from actions import CombatActionEntry, PlayerAction
from conditions import Condition
from pynput.keyboard import Key
from utils import key_to_delta, getRelativePath
from typing import TYPE_CHECKING, TypedDict

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
    def __init__(self, name: str = "Player", class_type: str = "warrior"):
        self.name = name
        self.class_type = class_type
        self.inventory = inventory.PlayerInventory()

        with open(getRelativePath("player_stats.json"), "r") as f:
            all_stats: dict[str, PlayerStats] = json.load(f)
            self.stats = all_stats[self.class_type]

        self.combat: CombatHandler | None = None
        self.speed = self.stats["base_stats"]["speed"]
        self.max_health = self.stats["base_stats"]["health"]
        self.health = self.max_health
        self.max_stamina = self.stats["base_stats"]["stamina"]
        self.stamina = self.max_stamina
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
    def from_json(cls, j):
        new_player = cls(name=j["name"], class_type=j["class_type"])
        new_player.inventory = inventory.from_json(j["inventory"])
        new_player.speed = j["speed"]
        new_player.max_health = j["max_health"]
        new_player.health = j["health"]
        new_player.max_stamina = j["max_stamina"]
        new_player.stamina = j["stamina"]
        return new_player

    def getTurnOptions(self, handler: CombatHandler) -> list[CombatActionEntry]:
        actions: list[CombatActionEntry] = [
            CombatActionEntry("Attack", self.attack),
            CombatActionEntry("Pass", lambda h: None),
            # (
            #     "kill other player",
            #     lambda h: h.select_character(
            #         lambda c: isinstance(c, Player) and not c is self
            #     )[0].takeDamage(h, 1000),
            #     "Hehe silly",
            # ),
            CombatActionEntry(
                "Fireball", self.fireball, "High single-target damage", 5
            ),
            CombatActionEntry(
                "Scorching Ray", self.scorching_ray, "Multi-target magic beam", 10
            ),
        ]
        for i in self.inventory.items:
            actions.extend(i.combat_actions)
        if utils.DEBUG:
            actions.append(
                CombatActionEntry(
                    "debug.win",
                    lambda h: [[c.takeDamage(h, 1000) for c in h.enemies.copy()], None][
                        1
                    ],
                    "Win.",
                )
            )
        return [action for action in actions if action.stamina_cost <= self.stamina]

    def action_menu(self, party: Party):
        actions: list[tuple[str, PlayerAction]] = [
            ("View Inventory", self.inventory_menu)
        ]

        # for i in self.inventory.items:
        #     actions.extend(i.player_actions)
        while True:
            option: int = menuHelper.menu("Actions", [ac[0] for ac in actions])
            if option != -1:
                actions[option][1](party, self)
            else:
                return

    def attack(self, handler: CombatHandler):
        if not self.inventory.weapon:
            return
        to_attack: Player | Enemy = handler.select_character(
            lambda c: not isinstance(c, Player)
        )[0]
        damage: int = self.inventory.weapon.damage
        for item in self.inventory.items:
            if isinstance(item, Relic):
                damage = item.dealDamage(damage, self, to_attack) or damage
        to_attack.takeDamage(handler, damage, self)

    def takeDamage(self, handler: CombatHandler, damage: int, attacker=None):
        for relic in self.inventory.items:
            if isinstance(relic, Relic):
                damage = relic.takeDamage(damage, attacker, self) or damage
        self.health -= damage
        if self.health <= 0:
            self.die(handler)

    def die(self, handler: CombatHandler):
        print(f"Player {self.name} dies!")
        for relic in self.inventory.items:
            if isinstance(relic, Relic):
                relic.die()
        for condition in self.conditions:
            condition.die()
        if self.health <= 0:
            handler.removePlayer(self)

    def pretty_print_turn_options(
        self,
        options: list[CombatActionEntry],
        selected: int,
        w: int,
        h: int,
    ) -> list[str]:
        content_width = w - 2
        content_height = h - 2
        out: list[str] = []
        out.append("┌" + "─" * content_width + "┐")
        for i in range(min(content_height, len(options))):
            opt = options[i]
            out.append(
                "│"
                + (("> " if i == selected else "  ") + opt.name).ljust(content_width)
                + "│"
            )
        out.append("└" + "─" * content_width + "┘")
        return out

    def turnStart(self, handler: CombatHandler):
        for relic in self.inventory.items:
            if isinstance(relic, Relic):
                relic.turnStart()
        for condition in self.conditions:
            condition.turnStart()
        op = self.getTurnOptions(handler)
        selectedOption = 0
        lastProvider = terminalDisplay.contextDisplay.messageProvider
        terminalDisplay.contextDisplay.messageProvider = (
            lambda w, h: self.pretty_print_turn_options(op, selectedOption, w, h)
        )
        lastDescProvider = terminalDisplay.descriptionDisplay.messageProvider

        def get_desc(w: int, h: int) -> list[str]:
            option = op[selectedOption]
            st_cst = ""
            if option.stamina_cost:
                st_cst = f"Stamina Cost: {option.stamina_cost} "
            if option.description or st_cst:
                return utils.boxify(w, h, f"{st_cst}{option.description}")
            return []

        terminalDisplay.descriptionDisplay.messageProvider = get_desc
        # terminalDisplay.combatDisplay.messageProvider = (
        #     lambda w, h:
        # )
        while True:
            selectedOption %= len(op)
            terminalDisplay.updateDisplays()
            while True:
                key = inputController.getKey()
                if key in key_to_delta:
                    selectedOption += key_to_delta[key]
                    break
                if key == Key.enter:
                    terminalDisplay.contextDisplay.messageProvider = lastProvider
                    terminalDisplay.descriptionDisplay.messageProvider = (
                        lastDescProvider
                    )
                    self.stamina -= op[selectedOption].stamina_cost
                    op[selectedOption].action(handler)
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

    def inventory_menu(self, party: Party, _):
        options = self.inventory.items
        optionStrs = [i.name for i in options]
        while True:
            option = menuHelper.menu("Pick an item", optionStrs)
            if option != -1:
                it = options[option]
                action_options: list[tuple[str, PlayerAction]] = [
                    (
                        "Move to party",
                        lambda party, player: self.moveItemToParty(party, it),
                    )
                ]
                action_options.extend(it.player_actions)
                act_options_strs = [ac[0] for ac in action_options]
                while True:
                    option = menuHelper.menu("Action to take:", act_options_strs)
                    if option != -1:
                        if action_options[option][1](party, self):
                            return
                    else:
                        break
            else:
                return

    def startCombat(self):
        for relic in self.inventory.items:
            if isinstance(relic, Relic):
                relic.combatStart()

    def leaveCombat(self):
        self.conditions = []

    def fireball(self, handler: CombatHandler):
        if not self.inventory.weapon:
            return
        to_attack: Player | Enemy = handler.select_character(
            lambda c: not isinstance(c, Player)
        )[0]
        damage: int = self.inventory.weapon.damage * 2
        for item in self.inventory.items:
            if isinstance(item, Relic):
                damage = item.dealDamage(damage, self, to_attack, "magic") or damage
        to_attack.takeDamage(handler, damage, self)

    def scorching_ray(self, handler: CombatHandler):
        to_attack: list[Player | Enemy] = handler.select_character(
            lambda c: not isinstance(c, Player), 3, 1
        )
        for c in to_attack:
            damage: int = 5
            for item in self.inventory.items:
                if isinstance(item, Relic):
                    damage = item.dealDamage(damage, self, c, "magic") or damage
            c.takeDamage(handler, damage, self)
