from item import Item
from party import Party
from utils import clear
import inputController
from pynput.keyboard import Key
from colorama import Fore, Style

key_to_delta = {
    Key.up: -1,
    Key.down: 1
}

class Shop:
    def __init__(self, items: list[tuple[Item, int]]):
        self.items: list[tuple[Item, int]] = items

    def pretty_print(self, funds: int = 0, selectedItem: int = -1):
        longestName = max([len(item[0].name) for item in self.items])
        additionalChars = max(0, longestName - 8)
        print("┌─────────────────" + "─" * additionalChars + "┐")
        print("│" + "Shop".center(17 + additionalChars) + "│")
        print("├─────────────────" + "─" * additionalChars + "┤")
        for i, (item, price) in enumerate(self.items):
            print(f"│{("> " if i == selectedItem else "  ")}{Fore.LIGHTRED_EX if price > funds else ""}{item.name.ljust(8 + additionalChars)}{Style.RESET_ALL} │ {f"{Fore.LIGHTYELLOW_EX}¢" if funds >= price else f"{Fore.LIGHTRED_EX}×"}{price:<3.0f}{Style.RESET_ALL}│")
        print("└─────────────────" + "─" * additionalChars + "┘")
            

    def displayShop(self, party: Party):
        selectedItem = 0
        while True:
            selectedItem %= len(self.items)
            clear()
            self.pretty_print(party.funds, selectedItem)
            while True:
                key = inputController.getKey()
                if key and key in key_to_delta.keys():
                    selectedItem += key_to_delta[key];
                    break
                if key == Key.enter:
                    price = self.items[selectedItem][1]
                    if party.funds >= price:
                        party.inventory.add(self.items[selectedItem][0])
                        party.funds -= price
                        del self.items[selectedItem]
                        break
