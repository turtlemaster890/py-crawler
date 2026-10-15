from typing import Callable

import room
import utils
import json
import terminalDisplay
import inputController
from pynput.keyboard import Key
from maze import maze
from party import Party
from pathlib import Path

SAVE_LOCATION: Path = utils.getRelativePath(Path("saves/"))
save_index = 0

save_file: Path = SAVE_LOCATION.joinpath(f"save_{save_index}.json")


def select_save_file() -> None:
    global save_file
    save_files: list[Path] = [p for p in SAVE_LOCATION.glob("*.json")]
    options: list[str] = [f"Save {p.name.split('_')[1].removesuffix(".json")}" for p in save_files]

    selected = 0
    hselected = 0
    lastProvider: Callable[[int, int], list[str]] | None = terminalDisplay.contextDisplay.messageProvider
    terminalDisplay.contextDisplay.messageProvider = lambda w, h: show_saves(
        w, h, options, selected, hselected
    )

    while True:
        selected %= len(options) + 1
        hselected %= 2
        terminalDisplay.updateDisplays()
        while True:
            key: Key | inputController.KeyCode | None = inputController.getKey()
            if key and key in utils.key_to_delta:
                selected += utils.key_to_delta[key]
                break
            if key in [Key.left, Key.right]:
                hselected += (key == Key.right) - (key == Key.left)
                break
            if key == Key.enter:
                if selected >= len(options):
                    save_file = SAVE_LOCATION.joinpath(f"save_{len(options)}.json")
                else:
                    if hselected == 0:
                        save_file = save_files[selected]
                    else:
                        save_files[selected].unlink()
                        del save_files[selected]
                        del options[selected]
                        break
                terminalDisplay.contextDisplay.messageProvider = lastProvider
                return


def show_saves(
    w: int, h: int, save_files: list[str], selected: int = -1, hselected: int = -1
) -> list[str]:
    nameSpace: int = w - 7
    # longestName = max([len(item[0].name) for item in self.items])
    # additionalChars = max(0, longestName - 8)
    out = []
    out.append("┌" + "─" * (w - 2) + "┐")
    out.append("│" + "Saves".center(w - 2) + "│")
    out.append("├" + "─" * (w - 2) + "┤")
    for i, save_file in enumerate(save_files):
        out.append(
            f"│{(">[" if i == selected and hselected == 0 else ("> " if i == selected else "  "))}{save_file[:nameSpace].ljust(nameSpace)}{"[×]" if selected == i and hselected == 1 else ("]× " if selected == i else " × ")}│"
        )
    out.append(
        f"│{("> " if selected == len(save_files) else "  ")}{"New Save".ljust(w - 5)} │"
    )
    out.append("└" + "─" * (w - 2) + "┘")
    return out


def save_maze(maze: maze):
    maze_rep: list[list[dict | None]] = []
    for row in maze:
        row_rep: list[dict | None] = []
        for rm in row:
            if isinstance(rm, room.Room):
                room_rep = rm.to_json()
                row_rep.append(room_rep)
            else:
                row_rep.append(None)
        maze_rep.append(row_rep)
    return maze_rep


def load_maze(maze_rep: list[list[dict | None]]) -> maze:
    mz = []
    for row_rep in maze_rep:
        row = []
        for room_rep in row_rep:
            if isinstance(room_rep, dict):
                rm = room.from_json(room_rep)
            else:
                rm = None
            row.append(rm)
        mz.append(row)
    return mz


def save(mz: maze, party: Party) -> None:
    SAVE_LOCATION.mkdir(parents=True, exist_ok=True)
    with open(save_file, "w") as f:
        json.dump({"maze": save_maze(mz), "party": party.to_json()}, f, indent=4)


def load(j) -> tuple[maze, Party]:
    return (load_maze(j["maze"]), Party.from_json(j["party"]))
