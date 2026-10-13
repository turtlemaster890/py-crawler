import os
import textwrap
import inputController
from typing import Callable
from pynput.keyboard import Key


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def boxify(w: int, h: int, message: str, squish: bool = True) -> list[str]:
    boxWidth = w - 2
    lines = textwrap.wrap(message, boxWidth - 2, max_lines=h - 2)
    if squish:
        boxHeight = min(len(lines), h - 2)
    else:
        boxHeight = h - 2
    out = []
    out.append("┌" + "─" * boxWidth + "┐")
    for i in range(boxHeight):
        if len(lines) > i:
            out.append(f"│ {lines[i].ljust(boxWidth - 2)} │")
        else:
            out.append(f"│{" " * boxWidth}│")
    out.append("└" + "─" * boxWidth + "┘")
    return out

def wait_for_enter():
    while True:
        key = inputController.getKey()
        if key == Key.enter:
            return

printSqs: dict[str, tuple[Callable, int]] = {}

def addPrintFunction(name: str, func: Callable, priority: int):
    printSqs[name] = (func, priority)

def removePrintFunction(name: str):
    del printSqs[name]

def printSequences():
    clear()
    order = list(printSqs.values())
    order.sort(key=lambda x: x[1]) #.sort(key = lambda x: x[1])
    for func in order:
        func[0]()

key_to_delta = {
    Key.up: -1,
    Key.down: 1
}

def getRelativePath(filename: str):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), filename))