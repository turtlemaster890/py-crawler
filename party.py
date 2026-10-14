from Pos import Pos
from player import Player
from inventory import Inventory
from item import Item
from inventory import Inventory
import terminalDisplay
import inputController
import utils
from pynput.keyboard import Key


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

    def move_to_member_menu(self, item: Item):
        selected = 0
        options = self.members
        lastProvider = terminalDisplay.contextDisplay.messageProvider
        terminalDisplay.contextDisplay.messageProvider = (
            lambda w, h: self.show_move_item_options(
                w, h, [m.name for m in options], selected
            )
        )
        while True:
            selected %= len(options) + 1
            terminalDisplay.updateDisplays()
            while True:
                key = inputController.getKey()
                if key and key in utils.key_to_delta:
                    selected += utils.key_to_delta[key]
                    break
                if key == Key.enter:
                    if selected < len(options):
                        self.moveItemToMember(options[selected], item)
                    terminalDisplay.contextDisplay.messageProvider = lastProvider
                    return

    def show_move_item_options(
        self, w: int, h: int, options: list[str], selected: int = -1
    ) -> list[str]:
        nameSpace = w - 5
        # longestName = max([len(item[0].name) for item in self.items])
        # additionalChars = max(0, longestName - 8)
        out = []
        out.append("┌" + "─" * (w - 2) + "┐")
        out.append("│" + "Move to".center(w - 2) + "│")
        out.append("├" + "─" * (w - 2) + "┤")
        for i, option in enumerate(options):
            out.append(
                f"│{("> " if i == selected else "  ")}{option[:nameSpace].ljust(nameSpace)} │"
            )
        out.append(
            f"│{("> " if selected == len(options) else "  ")}{"Cancel".ljust(w - 5)} │"
        )
        out.append("└" + "─" * (w - 2) + "┘")
        return out

    def item_menu(self, item: Item):
        selected = 0
        options = [("Move to player", lambda: self.move_to_member_menu(item))]
        lastProvider = terminalDisplay.contextDisplay.messageProvider
        terminalDisplay.contextDisplay.messageProvider = (
            lambda w, h: self.show_item_options(
                w, h, item, [option[0] for option in options], selected
            )
        )
        while True:
            selected %= len(options) + 1
            terminalDisplay.updateDisplays()
            while True:
                key = inputController.getKey()
                if key and key in utils.key_to_delta:
                    selected += utils.key_to_delta[key]
                    break
                if key == Key.enter:
                    if selected < len(options):
                        options[selected][1]()
                    terminalDisplay.contextDisplay.messageProvider = lastProvider
                    return

    def show_item_options(
        self, w: int, h: int, item: Item, options: list[str], selected: int = -1
    ) -> list[str]:
        nameSpace = w - 5
        # longestName = max([len(item[0].name) for item in self.items])
        # additionalChars = max(0, longestName - 8)
        out = []
        out.append("┌" + "─" * (w - 2) + "┐")
        out.append("│" + item.name.center(w - 2) + "│")
        out.append("├" + "─" * (w - 2) + "┤")
        for i, option in enumerate(options):
            out.append(
                f"│{("> " if i == selected else "  ")}{option[:nameSpace].ljust(nameSpace)} │"
            )
        out.append(
            f"│{("> " if selected == len(options) else "  ")}{"Cancel".ljust(w - 5)} │"
        )
        out.append("└" + "─" * (w - 2) + "┘")
        return out

    def inventory_menu(self):
        selected = 0
        lastProvider = terminalDisplay.contextDisplay.messageProvider
        terminalDisplay.contextDisplay.messageProvider = (
            lambda w, h: self.show_inventory(w, h, selected)
        )

        while True:
            selected %= len(self.inventory.items) + 1
            terminalDisplay.updateDisplays()
            while True:
                key = inputController.getKey()
                if key and key in utils.key_to_delta:
                    selected += utils.key_to_delta[key]
                    break
                if key == Key.enter:
                    if selected < len(self.inventory.items):
                        self.item_menu(self.inventory.items[selected])
                        break
                    terminalDisplay.contextDisplay.messageProvider = lastProvider
                    return

    def show_inventory(self, w: int, h: int, selected: int = -1) -> list[str]:
        nameSpace = w - 5
        # longestName = max([len(item[0].name) for item in self.items])
        # additionalChars = max(0, longestName - 8)
        out = []
        out.append("┌" + "─" * (w - 2) + "┐")
        out.append("│" + "Actions".center(w - 2) + "│")
        out.append("├" + "─" * (w - 2) + "┤")
        for i, option in enumerate(self.inventory.items):
            out.append(
                f"│{("> " if i == selected else "  ")}{option.name[:nameSpace].ljust(nameSpace)} │"
            )
        out.append(
            f"│{("> " if selected == len(self.inventory.items) else "  ")}{"Cancel".ljust(w - 5)} │"
        )
        out.append("└" + "─" * (w - 2) + "┘")
        return out

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
