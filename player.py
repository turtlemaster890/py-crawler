import json
from maze import Pos
from inventory import PlayerInventory
from item import Item, Weapon, Armor
import terminalDisplay
import inputController
from pynput.keyboard import Key
from utils import key_to_delta, getRelativePath
from typing import TYPE_CHECKING, Callable, TypedDict
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
    def __init__(self, pos: Pos, name: str = "Player", class_type: str = "warrior"):
        self.pos = pos
        self.name = name
        self.class_type = class_type
        self.inventory = PlayerInventory()

        with open(getRelativePath("player_stats.json"), "r") as f:
            all_stats: dict[str, PlayerStats] = json.load(f)
            self.stats = all_stats[self.class_type]

        self.combat: CombatHandler | None = None
        self.speed = self.stats["base_stats"]["speed"]
        self.max_health = self.stats["base_stats"]["health"]
        self.health = self.max_health
        self.max_stamina = self.stats["base_stats"]["stamina"]
        self.stamina = self.max_stamina
        self.inventory.equip(Weapon(self.stats["starting_items"]["weapon"]))
        self.inventory.equip(Armor(self.stats["starting_items"]["armor"]))
        for item in self.stats["starting_items"]["items"]:
            self.inventory.add(Item(item))
    
    def getTurnOptions(self, handler: CombatHandler) -> list[tuple[str, Callable[[CombatHandler], None]]]:
        return [
            ("pass", lambda h: None), 
            ("die", lambda h: self.takeDamage(h, 100)), 
            ("attack", self.attack),
            ("kill other player", lambda h: h.select_character(lambda c: isinstance(c, Player) and not c is self).takeDamage(h, 1000))
            ]

    def attack(self, handler: CombatHandler):
        if not self.inventory.weapon:
            return
        to_attack = handler.select_character(lambda c: not isinstance(c, Player))
        to_attack.takeDamage(handler, self.inventory.weapon.damage)

    def takeDamage(self, handler: CombatHandler, damage: int):
        self.health -= damage
        if self.health <= 0:
            self.die(handler)

    def die(self, handler: CombatHandler):
        print(f"Player {self.name} dies!")
        handler.removePlayer(self)

    def pretty_print_turn_options(self, options: list[tuple[str, Callable]], selected: int, w: int, h: int) -> list[str]:
        content_width = w - 2
        content_height = h - 2
        out: list[str] = []
        out.append("┌" + "─" * content_width + "┐")
        for i in range(min(content_height, len(options))):
            optName, optFunc = options[i]
            out.append("│" + (("> " if i == selected else "  ") + optName).ljust(content_width) + "│")
        out.append("└" + "─" * content_width + "┘")
        return out

    def turnStart(self, handler: CombatHandler):
        op = self.getTurnOptions(handler)
        selectedOption = 0
        terminalDisplay.contextDisplay.messageProvider = lambda w, h: self.pretty_print_turn_options(op, selectedOption, w, h)
        while True:
            selectedOption %= len(op)
            terminalDisplay.updateDisplays()
            while True:
                key = inputController.getKey()
                if key in key_to_delta:
                    selectedOption += key_to_delta[key]
                    break
                if key == Key.enter:
                    terminalDisplay.contextDisplay.messageProvider = None
                    op[selectedOption][1](handler)
                    return
        

    def moveItemToParty(self, party: Party, item: Item) -> bool:
        if item not in self.inventory: return False
        if not self.inventory.remove(item): return False
        if not party.inventory.add(item):
            self.inventory.add(item)
            return False
        return True