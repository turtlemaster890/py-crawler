from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar, TypeVar, dataclass_transform


class PacketError(Exception):
    pass


_registry: dict[str, type["Packet"]] = {}


class Packet:
    type: ClassVar[str]

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, **asdict(self)}  # type: ignore

    @staticmethod
    def from_dict(d: Any) -> "Packet":
        if not isinstance(d, dict):
            raise PacketError("Packet must be an object")
        cls = _registry.get(d.get("type", ""))
        if cls is None:
            raise PacketError(f"Unknown packet type {d.get("type")!r}")
        kwargs = {k: v for k, v in d.items() if k != "type"}
        try:
            return cls(**kwargs)
        except TypeError as e:
            raise PacketError(f"bad {cls.type} packet: {e}")


T = TypeVar("T")


@dataclass_transform(field_specifiers=(field,))
def packet(cls: type[T]) -> type[T]:
    """Registers packet"""
    nCls = dataclass(cls)
    nCls.type = nCls.__name__  # type: ignore
    _registry[nCls.type] = nCls  # type: ignore
    return nCls


# Shared
@dataclass
class TurnRow:
    name: str
    health: int
    av: int
    is_player: bool = False


@dataclass
class ChoiceRow:
    name: str
    health: int
    av: int
    index: int


def _coerce(items: list, cls) -> list:
    return [cls(**i) if isinstance(i, dict) else i for i in items]


# Client -> Server
@packet
class Join(Packet):
    characters: list[int]

    def __post_init__(self):
        if not all(type(i) is int for i in self.characters):
            raise PacketError("Characters must be whole numbers")


@packet
class Move(Packet):
    dir: str


@packet
class OptionChosen(Packet):
    option: int = 0


@packet
class CharactersChosen(Packet):
    selected: list[int] = field(default_factory=list)


@packet
class OpenActions(Packet):
    pass


@packet
class MenuChoice(Packet):
    option: int = -1


# Server -> Client
@packet
class Error(Packet):
    message: str


@packet
class Log(Packet):
    text: str
    typed: bool = False


@packet
class Snapshot(Packet):
    you: int | None
    width: int
    height: int
    squads: list[dict]
    rooms: list[dict]
    floor: int = 1
    funds: int = 0
    members: list[dict] = field(default_factory=list)


@packet
class CombatState(Packet):
    turn_order: list[TurnRow]

    def __post_init__(self):
        self.turn_order = _coerce(self.turn_order, TurnRow)


@packet
class CombatEnd(Packet):
    result: str


@packet
class ChooseOption(Packet):
    options: list[str]


@packet
class ChooseCharacters(Packet):
    options: list[ChoiceRow]
    count: int
    minimum: int

    def __post_init__(self):
        self.options = _coerce(self.options, ChoiceRow)


@packet
class Menu(Packet):
    title: str
    options: list[str]
    back: bool = True


@packet
class Roster(Packet):
    characters: list[dict]
