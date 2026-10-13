from typing import TYPE_CHECKING
from item import Item
if TYPE_CHECKING:
    from party import Party
import inputController
import terminalDisplay
from utils import key_to_delta
from pynput.keyboard import Key
from colorama import Fore, Style

class Shop:
    def __init__(self, items: list[tuple[Item, int]]):
        self.items: list[tuple[Item, int]] = items

    def to_json(self):
        return [(i.to_json(), c) for i, c in self.items]

    @classmethod
    def from_json(cls, j: list[tuple[dict, int]]):
        return cls([(Item.from_json(i), c) for i, c in j])
        
    def pretty_print(self, funds: int = 0, selectedItem: int = -1):
        longestName = max([len(item[0].name) for item in self.items])
        additionalChars = max(0, longestName - 8)
        print("┌─────────────────" + "─" * additionalChars + "┐")
        print("│" + "Shop".center(17 + additionalChars) + "│")
        print("├─────────────────" + "─" * additionalChars + "┤")
        for i, (item, price) in enumerate(self.items):
            print(f"│{("> " if i == selectedItem else "  ")}{Fore.LIGHTRED_EX if price > funds else ""}{item.name.ljust(8 + additionalChars)}{Style.RESET_ALL} │ {f"{Fore.LIGHTYELLOW_EX}¢" if funds >= price else f"{Fore.LIGHTRED_EX}×"}{price:<3.0f}{Style.RESET_ALL}│")
        print(f"│{("> " if selectedItem == len(self.items) else "  ")}{"Exit".ljust(15 + additionalChars)}│")
        print("└─────────────────" + "─" * additionalChars + "┘")

    def pretty_print_list(self, w: int, h: int, funds: int = 0, selectedItem: int = -1) -> list[str]:
        nameSpace = w - 11
        # longestName = max([len(item[0].name) for item in self.items])
        # additionalChars = max(0, longestName - 8)
        out = []
        out.append("┌" + "─" * (w - 2) + "┐")
        out.append("│" + "Shop".center(w - 2) + "│")
        out.append("├" + "─" * (w - 2) + "┤")
        for i, (item, price) in enumerate(self.items):
            out.append(f"│{("> " if i == selectedItem else "  ")}{Fore.LIGHTRED_EX if price > funds else ""}{item.name[:nameSpace].ljust(nameSpace)}{Style.RESET_ALL} │ {f"{Fore.LIGHTYELLOW_EX}¢" if funds >= price else f"{Fore.LIGHTRED_EX}×"}{price:<3.0f}{Style.RESET_ALL}│")
        out.append(f"│{("> " if selectedItem == len(self.items) else "  ")}{"Exit".ljust(w - 4)}│")
        out.append("└" + "─" * (w - 2) + "┘")
        return out
            

    def displayShop(self, party: Party):
        if len(self.items) == 0: return
        # utils.addPrintFunction("shop", lambda: self.pretty_print(party.funds, selectedItem), 2)
        terminalDisplay.contextDisplay.messageProvider = lambda w, h: self.pretty_print_list(w, h, party.funds, selectedItem)
        selectedItem = 0
        while True:
            if len(self.items) == 0:
                # utils.removePrintFunction("shop")
                terminalDisplay.contextDisplay.messageProvider = None
                return
            selectedItem %= len(self.items) + 1
            # clear()
            # self.pretty_print(party.funds, selectedItem)
            # utils.printSequences()
            terminalDisplay.updateDisplays()
            while True:
                key = inputController.getKey()
                if key and key in key_to_delta.keys():
                    selectedItem += key_to_delta[key] # type: ignore
                    break
                if key == Key.enter:
                    if selectedItem >= len(self.items):
                        # utils.removePrintFunction("shop")
                        terminalDisplay.contextDisplay.messageProvider = None
                        return
                    price = self.items[selectedItem][1]
                    if party.funds >= price:
                        party.inventory.add(self.items[selectedItem][0])
                        party.funds -= price
                        del self.items[selectedItem]
                        break