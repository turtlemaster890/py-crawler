import os
from pathlib import Path
import textwrap
import inputController
from typing import Any, Callable
from pynput.keyboard import Key

DEBUG_END_COMBAT = False
DEBUG_WIN_ACTION = True
DEBUG_VIEW = False


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def boxify(w: int, h: int, message: str, squish: bool = True) -> list[str]:
    boxWidth: int = w - 2
    lines: list[str] = textwrap.wrap(message, boxWidth - 2, max_lines=h - 2)
    if squish:
        boxHeight: int = min(len(lines), h - 2)
    else:
        boxHeight: int = h - 2
    out = []
    out.append("┌" + "─" * boxWidth + "┐")
    for i in range(boxHeight):
        if len(lines) > i:
            out.append(f"│ {lines[i].ljust(boxWidth - 2)} │")
        else:
            out.append(f"│{" " * boxWidth}│")
    out.append("└" + "─" * boxWidth + "┘")
    return out


def wait_for_enter() -> None:
    while True:
        key: Key | inputController.KeyCode | None = inputController.getKey()
        if key == Key.enter:
            return


printSqs: dict[str, tuple[Callable, int]] = {}


def addPrintFunction(name: str, func: Callable, priority: int) -> None:
    printSqs[name] = (func, priority)


def removePrintFunction(name: str) -> None:
    del printSqs[name]


def printSequences() -> None:
    clear()
    order: list[tuple[Callable[..., Any], int]] = list(printSqs.values())
    order.sort(key=lambda x: x[1])  # .sort(key = lambda x: x[1])
    for func in order:
        func[0]()


key_to_delta: dict[Key, int] = {Key.up: -1, Key.down: 1}


def getRelativePath(filename: str | Path) -> Path:
    return Path(os.path.join(os.path.dirname(__file__), filename))
