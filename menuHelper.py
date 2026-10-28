from typing import Callable

from pynput.keyboard import Key, KeyCode

import inputController
import terminalDisplay
import utils


def menu(menu_name: str, options: list[str], back: bool = True) -> int:
    selected = 0
    lastProvider = terminalDisplay.contextDisplay.messageProvider
    terminalDisplay.contextDisplay.messageProvider = lambda w, h: show_menu(
        w, h, menu_name, options, selected, back
    )

    while True:
        selected %= len(options) + (1 if back else 0)
        terminalDisplay.updateDisplays()
        while True:
            key: Key | KeyCode | None = inputController.getKey()
            if key and key in utils.key_to_delta:
                selected += utils.key_to_delta[key]
                break
            if key == Key.enter:
                if selected < len(options):
                    terminalDisplay.contextDisplay.messageProvider = lastProvider
                    terminalDisplay.updateDisplays()
                    return selected
                terminalDisplay.contextDisplay.messageProvider = lastProvider
                terminalDisplay.updateDisplays()
                return -1


def inputMenu(menu_name: str, max_len: int = -1) -> str:
    o = ""
    lastProvider: Callable[[int, int], list[str]] | None = (
        terminalDisplay.contextDisplay.messageProvider
    )
    terminalDisplay.contextDisplay.messageProvider = lambda w, h: show_input_menu(
        w, h, menu_name, o
    )
    while True:
        terminalDisplay.updateDisplays()
        while True:
            key: Key | KeyCode | None = inputController.getKey()
            if key:
                if key == Key.backspace:
                    if len(o) > 0:
                        o = o[:-1]
                elif key == Key.space:
                    o += " "
                elif key == Key.enter:
                    if len(o) > 0:
                        terminalDisplay.contextDisplay.messageProvider = lastProvider
                        return o
                elif isinstance(key, KeyCode) and key.char:
                    if len(o) < max_len and max_len != -1:
                        o += key.char
                break


def show_menu(
    w: int,
    h: int,
    title: str,
    options: list[str],
    selected: int = -1,
    back: bool = True,
) -> list[str]:
    nameSpace: int = w - 5
    maxOptions: int = h - 4 - back
    # longestName = max([len(item[0].name) for item in self.items])
    # additionalChars = max(0, longestName - 8)
    out = []
    out.append("┌" + "─" * (w - 2) + "┐")
    out.append("│" + title.center(w - 2) + "│")
    out.append("├" + "─" * (w - 2) + "┤")
    start_point = 0
    if selected != -1 and selected >= maxOptions:
        start_point = selected - maxOptions + (selected < len(options))
    for i, option in enumerate(options):
        if i < start_point:
            continue
        if i >= start_point + maxOptions:
            continue
        out.append(
            f"│{("> " if i == selected else "  ")}{option[:nameSpace].ljust(nameSpace)} │"
        )
    if back:
        out.append(
            f"│{("> " if selected == len(options) else "  ")}{"Back".ljust(w - 5)} │"
        )
    out.append("└" + "─" * (w - 2) + "┘")
    return out


def show_input_menu(w: int, h: int, title: str, curr_output: str) -> list[str]:
    out = []
    out.append("┌" + "─" * (w - 2) + "┐")
    out.append("│" + title.center(w - 2) + "│")
    out.append("├" + "─" * (w - 2) + "┤")
    out.append("│" + curr_output[: w - 2].ljust(w - 2) + "│")
    out.append("└" + "─" * (w - 2) + "┘")
    return out
