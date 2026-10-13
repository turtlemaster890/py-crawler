from Pos import Pos
from player import Player
from inventory import Inventory
from item import Item
from inventory import Inventory


class Party:
    def __init__(self, pos: Pos, members: list[Player]):
        self.pos = pos
        self.discovered_positions: set[Pos] = {pos}
        self.members = members
        self.inventory = Inventory()
        self.funds = 0

    def moveItemToMember(self, member: Player, item: Item) -> bool:
        if item not in self.inventory:
            return False
        if not self.inventory.remove(item):
            return False
        if not member.inventory.add(item):
            self.inventory.add(item)
            return False
        return True

    def to_json(self):
        return {
            "pos": self.pos.to_json(),
            "discovered": [p.to_json() for p in self.discovered_positions],
            "members": [m.to_json() for m in self.members],
            "inventory": self.inventory.to_json(),
            "funds": self.funds,
        }

    @classmethod
    def from_json(cls, j):
        new_party = cls(
            Pos.from_json(j["pos"]), [Player.from_json(p) for p in j["members"]]
        )
        new_party.discovered_positions = set(
            [Pos.from_json(p) for p in j.get("discovered", {new_party.pos})]
        )
        new_party.inventory = Inventory.from_json(j["inventory"])
        new_party.funds = j["funds"]
        return new_party
