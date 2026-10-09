from item import Item
from party import Party
from utils import clear
import inputController
from pynput.keyboard import Key

key_to_delta = {
    Key.up: -1,
    Key.down: 1
}

class Shop:
    def __init__(self, items: list[tuple[Item, int]]):
        self.items: list[tuple[Item, int]] = items

    def pretty_print(self, selectedItem: int = -1):
        longestName = max([len(item[0].name) + 2 for item in self.items])
        additionalChars = max(0, 12 - longestName)
        print("┌─────────────────" + "─" * additionalChars + "┐")
        print("│" + "Shop".center(17 + additionalChars) + "│")
        print("├─────────────────" + "─" * additionalChars + "┤")
        for i, (item, price) in enumerate(self.items):
            print(f"│{(("> " if i == selectedItem else "  ") + item.name).ljust(10 + additionalChars)} │ ¢{price:<3.0f}│")
        print("└─────────────────" + "─" * additionalChars + "┘")
            

    def displayShop(self, party: Party):
        selectedItem = 0
        while True:
            clear()
            self.pretty_print(selectedItem)
            while True:
                key = inputController.getKey()
                if key and key in key_to_delta.keys():
                    selectedItem += key_to_delta[key];
                    selectedItem %= len(self.items)
                    break
