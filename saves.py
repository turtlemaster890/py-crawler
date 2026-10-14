import room
import utils
import json
import terminalDisplay
import inputController
from pynput.keyboard import Key
from maze import maze
from party import Party
from pathlib import Path

SAVE_LOCATION = utils.getRelativePath(Path("saves/"))
save_index = 0

save_file = SAVE_LOCATION.joinpath(f"save_{save_index}.json")


def select_save_file():
    global save_file
    save_files = [p for p in SAVE_LOCATION.glob("*.json")]
    options = [f"Save {p.name.split('_')[1].removesuffix(".json")}" for p in save_files]

    selected = 0
    terminalDisplay.contextDisplay.messageProvider = lambda w, h: show_saves(
        w, h, options, selected
    )

    while True:
        selected %= len(options) + 1
        terminalDisplay.updateDisplays()
        while True:
            key = inputController.getKey()
            if key and key in utils.key_to_delta:
                selected += utils.key_to_delta[key]
                break
            if key == Key.enter:
                if selected >= len(options):
                    save_file = SAVE_LOCATION.joinpath(f"save_{len(options)}.json")
                else:
                    save_file = save_files[selected]
                terminalDisplay.contextDisplay.messageProvider = None
                return


def show_saves(w: int, h: int, save_files: list[str], selected: int = -1) -> list[str]:
    nameSpace = w - 5
    # longestName = max([len(item[0].name) for item in self.items])
    # additionalChars = max(0, longestName - 8)
    out = []
    out.append("┌" + "─" * (w - 2) + "┐")
    out.append("│" + "Shop".center(w - 2) + "│")
    out.append("├" + "─" * (w - 2) + "┤")
    for i, save_file in enumerate(save_files):
        out.append(
            f"│{("> " if i == selected else "  ")}{save_file[:nameSpace].ljust(nameSpace)} │"
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


def save(mz: maze, party: Party):
    SAVE_LOCATION.mkdir(parents=True, exist_ok=True)
    with open(save_file, "w") as f:
        json.dump({"maze": save_maze(mz), "party": party.to_json()}, f, indent=4)


def load(j) -> tuple[maze, Party]:
    return (load_maze(j["maze"]), Party.from_json(j["party"]))
