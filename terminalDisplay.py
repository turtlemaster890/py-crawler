from typing import Callable
import time
import utils


def moveCursor(x: int, y: int):
    print(f"\033[{y + 1};{x + 1}H", end="", flush=True)


class DisplayArea:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        messageProvider: Callable[[int, int], list[str]] | None = None,
        wrap: bool = False,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.messageProvider = messageProvider
        self.wrap = wrap

    def print_boxify(self, message: str):
        self.print(utils.boxify(self.width, self.height, message))

    def type_print(self, message: str):
        total = ""
        for char in message:
            total += char
            self.print_boxify(total)
            time.sleep(0.05)

    def print(self, text: list[str] = []):
        for i in range(self.height):
            moveCursor(self.x, self.y + i)
            print(" " * self.width)
        if self.messageProvider and len(text) == 0:
            text = self.messageProvider(self.width, self.height)
        for i in range(self.height):
            moveCursor(self.x, self.y + i)
            if i < len(text):
                print(text[i], end="", flush=True)


mazeDisplay = DisplayArea(0, 0, 30, 15)

combatDisplay = DisplayArea(31, 0, 35, 15)

contextDisplay = DisplayArea(0, 15, 30, 10)

combatDisplay = DisplayArea(31, 15, 35, 15)

displays = [mazeDisplay, combatDisplay, contextDisplay, combatDisplay]


def updateDisplays():
    for d in displays:
        d.print()
