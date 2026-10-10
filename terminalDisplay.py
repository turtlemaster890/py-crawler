from typing import Callable
import utils

class DisplayArea:
    def __init__(self, x: int, y: int, width: int, height: int, messageProvider: Callable[[int, int], list[str]] | None = None, wrap: bool = False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.messageProvider = messageProvider
        self.wrap = wrap

    def print(self, text: list[str] = []):
        if self.messageProvider:
            text = self.messageProvider(self.width, self.height)
        for i in range(self.height):
            print(f"\033[{self.y + i + 1};{self.x + 1}H", end="", flush=True)
            if i < len(text):
                print(text[i], end="", flush=True)

mazeDisplay = DisplayArea(0, 0, 15, 15)

combatDisplay = DisplayArea(16, 0, 25, 15)

contextDisplay = DisplayArea(0, 16, 20, 10)

displays = [mazeDisplay, combatDisplay, contextDisplay]
def updateDisplays():
    utils.clear()
    for d in displays:
        d.print()