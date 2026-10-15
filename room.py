from typing import Callable, Self

from direction import direction
from colorama import Fore
import enemy
from shop import Shop
from item import Item


class Room:
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
    def __init__(self, connections: set[direction] | None = None) -> None:
        super().__init__(connections)
        self.enemies = []
        self.colour: str = Fore.GREEN
        self.selectedColour: str = Fore.LIGHTGREEN_EX

    def to_json(self):
        j = super().to_json()
        j["room_type"] = "start"
        return j


class EndRoom(Room):
    def __init__(self, connections: set[direction] | None = None) -> None:
        super().__init__(connections, enemies=[enemy.StoneTitan()])
        self.colour: str = Fore.RED
        self.selectedColour: str = Fore.LIGHTRED_EX

    def to_json(self):
        j = super().to_json()
        j["room_type"] = "end"
        return j


class ShopRoom(Room):
    def __init__(self, connections: set[direction] | None = None) -> None:
        super().__init__(connections)
        self.has_action = True
        self.enemies = []
        self.shop = Shop(
            [
                (Item("Joe's Toe"), 50),
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


str_to_room_type = {"room": Room, "start": StartRoom, "end": EndRoom, "shop": ShopRoom}


def from_json(j: dict[str, object]):
    _class = str_to_room_type.get(j["room_type"], Room)  # type: ignore
    return _class.from_json(j)
