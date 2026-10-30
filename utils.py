import os
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Any

DEBUG_END_COMBAT = False
DEBUG_WIN_ACTION = True
DEBUG_VIEW = True


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
    from pynput.keyboard import Key, KeyCode

    import inputController

    while True:
        key: Key | KeyCode | None = inputController.getKey()
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


def __getattr__(name) -> Any:
    if name == "key_to_delta":
        from pynput.keyboard import Key, KeyCode

        _key_to_delta: dict[Key | KeyCode | None, int] = {Key.up: -1, Key.down: 1}
        globals()[name] = _key_to_delta
        return _key_to_delta


def getRelativePath(filename: str | Path) -> Path:
    return Path(os.path.join(os.path.dirname(__file__), filename))
