from typing import Self

from actions import PartyAction
from direction import direction
from colorama import Fore
import menuHelper
from shop import Shop
from enemy import Enemy, Mimic
import enemy
import terminalDisplay
from party import Party
import random
import utils
from combatHandler import CombatHandler


class Room:
    description = ""
    entry_message: str = ""

    def __init__(
        self,
        connections: set[direction] | None = None,
        enemies: list[Enemy] | None = None,
    ) -> None:
        if connections is None:
            connections = set()
        if enemies is None:
            enemies = []
        self.connections: set[direction] = connections
        self.enemies: list[Enemy] = enemies
        self.colour: str = Fore.LIGHTBLACK_EX
        self.selectedColour: str = Fore.WHITE
        self.room_actions: list[tuple[str, PartyAction]] = []

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

    def get_room_actions(self) -> list[tuple[str, PartyAction]]:
        return self.room_actions

    def has_connection(self, direction: direction) -> bool:
        return direction in self.connections

    def make_connection(self, direction: direction) -> None:
        self.connections.add(direction)

    def list_connections(self) -> set[direction]:
        o: set[direction] = set()
        for d in direction:
            if self.has_connection(d):
                o.add(d)
        return o

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
    entry_message = "The floor trembles. A Stone Titan drags itself upright, its core glowing faintly."

    def __init__(self, connections: set[direction] | None = None, enemies=None) -> None:
        super().__init__(connections, enemies=None)
        self.colour: str = Fore.RED
        self.selectedColour: str = Fore.LIGHTRED_EX

    @property
    def description(self) -> str:
        if self.enemies:
            return "A vast chamber, filled with stale air. The air hums with a low, grinding vibration."
        return (
            "The Stone Titan's remains lie scattered. A stairway is open in the floor."
        )

    def get_room_actions(self):
        actions = list(self.room_actions)
        if not self.enemies:
            actions.append(("Descend Stairs", self.descend))
        return actions

    def descend(self, party: Party, room) -> bool:
        choice = menuHelper.menu(
            f"Descend to floor {party.floor + 1}?", ["Descend", "Stay"], False
        )
        if choice == 0:
            party.descent_requested = True
        return True

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
        self.shop = Shop()
        self.colour: str = Fore.YELLOW
        self.selectedColour: str = Fore.LIGHTYELLOW_EX
        self.room_actions = [("Open Shop", self.shop.displayShop)]

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

    def open_chest(self, party: Party, room):
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
            return True
        else:
            terminalDisplay.contextDisplay.print_boxify(
                f"The chest bites {triggering_player.name}!"
            )
            utils.wait_for_enter()
            mimic = Mimic()
            mimic.scale(party.floor)
            mimic.speed = 10000
            handler = CombatHandler(party, party.members, [mimic])
            mimic.speed = 85
            return handler

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


class LockedRoom(Room):
    description = "A padlocked gate stands at the exits to this room."

    def __init__(
        self, connections: set[direction] | None = None, enemies: list[Enemy] = []
    ) -> None:
        super().__init__(connections, [])
        self.locked_connections: set[direction] = set()
        self.locked = True

    def make_connection(self, direction: direction) -> None:
        self.locked_connections.add(direction)
        # return super().make_connection(direction)

    def has_connection(self, direction: direction) -> bool:
        if super().has_connection(direction):
            return True
        if direction in self.locked_connections and not self.locked:
            return True
        return False

    def unlock(self, party: Party):
        self.locked = False

    def to_json(self):
        j = super().to_json()
        j["room_type"] = "locked"
        j["locked_connections"] = [c.name for c in self.locked_connections]
        j["locked"] = self.locked
        return j

    @classmethod
    def from_json(cls, j) -> Self:
        new_room = super().from_json(j)
        new_room.locked = j["locked"]
        new_room.locked_connections = {direction[d] for d in j["locked_connections"]}
        return new_room


str_to_room_type = {
    "room": Room,
    "start": StartRoom,
    "end": EndRoom,
    "shop": ShopRoom,
    "chest": ChestRoom,
    "locked": LockedRoom,
}


def from_json(j: dict[str, object]):
    _class = str_to_room_type.get(j["room_type"], Room)  # type: ignore
    return _class.from_json(j)
