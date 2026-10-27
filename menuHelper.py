from pynput.keyboard import Key

import inputController
import terminalDisplay
import utils


def menu(menu_name: str, options: list[str], back: bool = True) -> int | None:
    selected = 0
    lastProvider = terminalDisplay.contextDisplay.messageProvider
    terminalDisplay.contextDisplay.messageProvider = lambda w, h: show_menu(
        w, h, menu_name, options, selected, back
    )

    while True:
        selected %= len(options) + (1 if back else 0)
        terminalDisplay.updateDisplays()
        while True:
            key: Key | inputController.KeyCode | None = inputController.getKey()
            if key and key in utils.key_to_delta:
                selected += utils.key_to_delta[key]
                break
            if key == Key.enter:
                if selected < len(options):
                    terminalDisplay.contextDisplay.messageProvider = lastProvider
                    return selected
                terminalDisplay.contextDisplay.messageProvider = lastProvider
                return


def show_menu(
    w: int,
    h: int,
    title: str,
    options: list[str],
    selected: int = -1,
    back: bool = True,
) -> list[str]:
    nameSpace: int = w - 5
    # longestName = max([len(item[0].name) for item in self.items])
    # additionalChars = max(0, longestName - 8)
    out = []
    out.append("┌" + "─" * (w - 2) + "┐")
    out.append("│" + title.center(w - 2) + "│")
    out.append("├" + "─" * (w - 2) + "┤")
    for i, option in enumerate(options):
        out.append(
            f"│{("> " if i == selected else "  ")}{option[:nameSpace].ljust(nameSpace)} │"
        )
    if back:
        out.append(
            f"│{("> " if selected == len(options) else "  ")}{"Back".ljust(w - 5)} │"
        )
    out.append("└" + "─" * (w - 2) + "┘")
    return out
