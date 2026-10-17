from typing import Callable, Self

from direction import direction
from colorama import Fore
import enemy
from shop import Shop
from item import *
import terminalDisplay
import party
import random
import utils
from combatHandler import CombatHandler


class Room:
    description = ""

    def __init__(
        self,
        connections: set[direction] | None = None,
        enemies: list[enemy.enemy] | None = None,
    ) -> None:
        if connections is None:
            connections = set()
        if enemies is None:
            enemies = []
        self.connections: set[direction] = connections
        self.enemies: list[enemy.enemy] = enemies
        self.colour: str = Fore.LIGHTBLACK_EX
        self.selectedColour: str = Fore.WHITE
        self.room_actions = []

    def to_json(self):
        return {
            "room_type": "room",
            "connections": [c.name for c in self.connections],
            "enemies": [enemy.to_json() for enemy in self.enemies],
            "colour": self.colour,
            "selected_colour": self.selectedColour,
        }

    @classmethod
    def from_json(cls, j) -> Self:
        new_room: Self = cls({direction[d] for d in j["connections"]})
        new_room.enemies = [enemy.from_json(e) for e in j["enemies"]]
        new_room.colour = j["colour"]
        new_room.selectedColour = j["selected_colour"]
        return new_room

    def has_connection(self, direction: direction) -> bool:
        return direction in self.connections

    def make_connection(self, direction: direction) -> None:
        self.connections.add(direction)

    def __repr__(self) -> str:
        return f"R({[d.name for d in self.connections]})"


class StartRoom(Room):
    description = "An empty room."

    def __init__(self, connections: set[direction] | None = None, enemies=None) -> None:
        super().__init__(connections)
        self.enemies = []
        self.colour: str = Fore.GREEN
        self.selectedColour: str = Fore.LIGHTGREEN_EX

    def to_json(self):
        j = super().to_json()
        j["room_type"] = "start"
        return j


class EndRoom(Room):
    def __init__(self, connections: set[direction] | None = None, enemies=None) -> None:
        super().__init__(connections, enemies=[enemy.StoneTitan()])
        self.colour: str = Fore.RED
        self.selectedColour: str = Fore.LIGHTRED_EX

    def to_json(self):
        j = super().to_json()
        j["room_type"] = "end"
        return j


class ShopRoom(Room):
    description = "A creature has set up a stall in this room."

    def __init__(self, connections: set[direction] | None = None, enemies=None) -> None:
        super().__init__(connections)
        self.has_action = True
        self.enemies = []
        self.shop = Shop(
            [
                (ManaBooster(), 50),
                (Item("Bob's Job"), 100),
                (Item("Floop's Goop"), 500),
            ]
        )
        self.colour: str = Fore.YELLOW
        self.selectedColour: str = Fore.LIGHTYELLOW_EX
        self.room_actions: list[tuple[str, Callable[..., None]]] = [
            ("Open Shop", self.shop.displayShop)
        ]

    def to_json(self):
        j = super().to_json()
        j["shop"] = self.shop.to_json()
        j["room_type"] = "shop"
        return j

    @classmethod
    def from_json(cls, j) -> Self:
        new_room: Self = super(ShopRoom, cls).from_json(j)
        new_room.shop = Shop.from_json(j["shop"])
        new_room.room_actions = [("Open Shop", new_room.shop.displayShop)]
        return new_room


class ChestRoom(Room):
    description = "A lone chest stands in the middle of this room."

    def __init__(self, connections: set[direction] | None = None, enemies=None) -> None:
        super().__init__(connections)
        self.chest_opened = False
        self.room_actions = [("Open Chest", self.open_chest)]

    def open_chest(self, party: party.Party):
        self.chest_opened = True
        self.room_actions = []
        self.description = "An opened chest stands in the middle of this room."
        triggering_player = random.choice(party.members)
        terminalDisplay.contextDisplay.print_boxify(
            f"{triggering_player.name} opens the chest."
        )
        utils.wait_for_enter()
        if random.randint(0, 1):
            terminalDisplay.contextDisplay.print_boxify("Contained inside is ¢300!")
            utils.wait_for_enter()
            party.funds += 300
        else:
            terminalDisplay.contextDisplay.print_boxify(
                f"The chest bites {triggering_player.name}!"
            )
            utils.wait_for_enter()
            return CombatHandler(party, party.members, [enemy.Mimic()])

    def to_json(self):
        j = super().to_json()
        j["room_type"] = "chest"
        j["chest_opened"] = self.chest_opened
        return j

    @classmethod
    def from_json(cls, j) -> Self:
        new_room = super().from_json(j)
        new_room.chest_opened = j["chest_opened"]
        if new_room.chest_opened:
            new_room.room_actions = []
            new_room.description = "An opened chest stands in the middle of this room."
        return new_room


str_to_room_type = {
    "room": Room,
    "start": StartRoom,
    "end": EndRoom,
    "shop": ShopRoom,
    "chest": ChestRoom,
}


def from_json(j: dict[str, object]):
    _class = str_to_room_type.get(j["room_type"], Room)  # type: ignore
    return _class.from_json(j)
