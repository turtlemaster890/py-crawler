from typing import Any, Callable, TYPE_CHECKING

from Pos import Pos
import menuHelper
from player import Player
from inventory import Inventory, group_items, stack_label
from item import Armor, Item, Weapon
from inventory import Inventory
import terminalDisplay
import inputController
import utils
from squad import Squad
from pynput.keyboard import Key

if TYPE_CHECKING:
    from room import Room


class Party:
    def __init__(self, pos: Pos, members: list[Player]):
        self.floor = 1
        self.descent_requested = False
        self.discovered_positions: set[Pos] = {pos}
        self.members = members
        self.inventory = Inventory()
        self.funds = 0
        self.squads = [Squad(pos, list(members))]

    def moveItemToMember(self, member: Player, item: Item) -> bool:
        if item not in self.inventory:
            return False
        if not self.inventory.remove(item):
            return False
        if not isinstance(item, Weapon) and not isinstance(item, Armor):
            if not member.inventory.add(item):
                self.inventory.add(item)
                return False
        else:
            returnedItem = member.inventory.equip(item)
            if returnedItem:
                self.inventory.add(returnedItem)
            return True
        return True

    def moveStackToMember(self, member: Player, item: Item) -> int:
        same = [
            i
            for i in self.inventory.items
            if i.item_type == item.item_type and i.name == item.name
        ]
        return sum(self.moveItemToMember(member, i) for i in same)

    def move_to_member_menu(self, item: Item, count: int = 1):
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
                        if count > 1:
                            self.moveStackToMember(options[selected], item)
                        else:
                            self.moveItemToMember(options[selected], item)
                        terminalDisplay.contextDisplay.messageProvider = lastProvider
                        terminalDisplay.updateDisplays()
                        return True
                    terminalDisplay.contextDisplay.messageProvider = lastProvider
                    terminalDisplay.updateDisplays()

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
            f"│{("> " if selected == len(options) else "  ")}{"Back".ljust(w - 5)} │"
        )
        out.append("└" + "─" * (w - 2) + "┘")
        return out

    def item_menu(self, item: Item, room: Room, count: int = 1):
        selected = 0
        options: list[tuple[str, Callable[[], Any]]] = [
            ("Move to player", lambda: self.move_to_member_menu(item))
        ]
        if count > 1 and not isinstance(item, (Weapon, Armor)):
            options.append(
                (
                    f"Move all {count} to player",
                    lambda: self.move_to_member_menu(item, count),
                )
            )
        options.extend([(a[0], lambda: a[1](self, room)) for a in item.party_actions])
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
                        if options[selected][1]():
                            terminalDisplay.contextDisplay.messageProvider = (
                                lastProvider
                            )
                            return
                    else:
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
            f"│{("> " if selected == len(options) else "  ")}{"Back".ljust(w - 5)} │"
        )
        out.append("└" + "─" * (w - 2) + "┘")
        return out

    def inventory_menu(self, party: Party, room):
        # selected = 0
        # lastProvider = terminalDisplay.contextDisplay.messageProvider
        # terminalDisplay.contextDisplay.messageProvider = (
        #     lambda w, h: self.show_inventory(w, h, selected)
        # )

        # while True:
        #     selected %= len(self.inventory.items) + 1
        #     terminalDisplay.updateDisplays()
        #     while True:
        #         key = inputController.getKey()
        #         if key and key in utils.key_to_delta:
        #             selected += utils.key_to_delta[key]
        #             break
        #         if key == Key.enter:
        #             if selected < len(self.inventory.items):
        #                 self.item_menu(self.inventory.items[selected])
        #                 break
        #             terminalDisplay.contextDisplay.messageProvider = lastProvider
        #             return
        while True:
            groups = group_items(self.inventory.items)
            option = menuHelper.menu("Items", [stack_label(i, n) for i, n in groups])
            if option == -1:
                return
            item, count = groups[option]
            if self.item_menu(item, room, count):
                return

    def players_menu(self, party: Party, room):
        options: list[Player] = self.members
        optionStrs: list[str] = [plr.name for plr in options]
        while True:
            option = menuHelper.menu("Player", optionStrs)
            if option != -1:
                options[option].action_menu(self)
            else:
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
            f"│{("> " if selected == len(self.inventory.items) else "  ")}{"Back".ljust(w - 5)} │"
        )
        out.append("└" + "─" * (w - 2) + "┘")
        return out

    def create_squad(self, pos: Pos, characters: list[Player]):
        if not characters:
            raise ValueError("squad character list is empty")
        if len(characters) != len(set(characters)):
            raise ValueError("squad has duplicate characters")
        for character in characters:
            if character in self.members:
                continue
            else:
                raise ValueError(character.name + " is not in the party")
        for squad in self.squads:
            for character in characters:
                if character not in squad.characters:
                    continue
                else:
                    raise ValueError(character.name + " is in another squad")
        squad = Squad(pos, list(characters))
        self.squads.append(squad)
        return squad

    # TODO: save all squads

    def to_json(self):
        return {
            "pos": self.squads[0].pos.to_json(),
            "discovered": [p.to_json() for p in self.discovered_positions],
            "members": [m.to_json() for m in self.members],
            "inventory": self.inventory.to_json(),
            "funds": self.funds,
            "floor": self.floor,
        }

    @classmethod
    def from_json(cls, j):
        new_party = cls(
            Pos.from_json(j["pos"]), [Player.from_json(p) for p in j["members"]]
        )
        new_party.discovered_positions = set(
            [Pos.from_json(p) for p in j.get("discovered", {new_party.squads[0].pos})]
        )
        new_party.inventory = Inventory.from_json(j["inventory"])
        new_party.funds = j["funds"]
        new_party.floor = j.get("floor", 1)
        return new_party
