import socket
import combatHandler
from enemy import Enemy
import menuHelper
from netutil import MessageSocket
from direction import direction
from maze import pretty_print_list
from Pos import Pos
from packets import (
    CharactersChosen,
    ChooseCharacters,
    ChooseOption,
    CombatEnd,
    CombatState,
    Error,
    Join,
    Log,
    Move,
    OptionChosen,
    Packet,
    Snapshot,
    TurnRow,
)
from player import Player
from room import Room
import terminalDisplay
import inputController
from pynput.keyboard import Key
import time
from turnEntry import TurnEntry
import utils
import colorama
import queue
import threading

KEYS = {Key.up: "UP", Key.down: "DOWN", Key.left: "LEFT", Key.right: "RIGHT"}


def turn_order_lines(rows: list[TurnRow], w: int, h: int):
    out = []
    name_space = w - 13
    out.append("┌" + "─" * (w - 2) + "┐")
    out.append("│" + "TURN ORDER".center(w - 2) + "│")
    out.append("├" + "─" * (w - 2) + "┤")
    for row in rows:
        name = f"{row.name} ({row.health}♥)"[:name_space].ljust(name_space)
        out.append(f"│ {name} │ {row.av:<3} AV │")
    out.append("└" + "─" * (w - 2) + "┘")
    return out


def build_view(snap: Snapshot):
    width, height = snap.width, snap.height

    grid: list[list[Room | None]] = [
        [None for _ in range(width)] for _ in range(height)
    ]
    discovered = set()

    for entry in snap.rooms:
        pos = Pos.from_json(entry["pos"])
        dirs = {direction[name] for name in entry["connections"]}

        room = Room(dirs)
        room.colour = entry["colour"]
        room.selectedColour = entry["selected_colour"]
        room.description = entry["description"]

        grid[pos.y][pos.x] = room
        discovered.add(pos)

    my_pos = Pos()
    if snap.you is not None:
        my_pos = Pos.from_json(snap.squads[snap.you]["pos"])

    return grid, discovered, my_pos


def render(snap: Snapshot):
    grid, discovered, my_pos = build_view(snap)
    here = grid[my_pos.y][my_pos.x]
    description = here.description if here is not None else ""
    terminalDisplay.mazeDisplay.messageProvider = lambda w, h: pretty_print_list(
        w, h, grid, discovered, my_pos, floor=snap.floor
    )
    terminalDisplay.descriptionDisplay.messageProvider = lambda w, h: utils.boxify(
        w, h, description
    )

    terminalDisplay.updateDisplays()


def receiver(ms: MessageSocket, inbox: queue.Queue):
    try:
        while True:
            msg = ms.recv()
            inbox.put(msg)
            if msg is None:
                return
    finally:
        inbox.put(None)


turn_rows: list[TurnRow]


def handle(msg: Packet):
    # if isinstance(msg, dict):
    global turn_rows
    # kind = msg.get("type")
    match msg:
        case Snapshot():
            render(msg)
        case Error(message=m):
            say(m)
        case Log(text=t, typed=typ):
            if typ:
                terminalDisplay.contextDisplay.type_print(t)
            else:
                terminalDisplay.contextDisplay.print_boxify(t)
        case CombatState(turn_order=rows):
            turn_rows = rows
            terminalDisplay.combatDisplay.print()
        case CombatEnd(result=r):
            turn_rows = []
            terminalDisplay.combatDisplay.print()
            say(r)
        case ChooseOption(options=opts):
            if len(opts) < 1:
                return
            option = menuHelper.menu("Choose option", opts, False)
            assert option is not None
            ms.send(OptionChosen(option))
        case ChooseCharacters(options=opts, count=c, minimum=m):
            if len(opts) < 1:
                return
            entries: list[TurnEntry] = []
            for row in turn_rows:
                char = Player(row.name) if row.is_player else Enemy(row.name)
                char.health = row.health
                entries.append(TurnEntry(row.av, char))
            # entries: list[TurnEntry] = [
            #     TurnEntry(
            #         row["av"],
            #         enemy(row["name"]) if row["is_player"] else Player(row["name"]),
            #     )
            #     for row in turn_rows
            # ]
            # passedOptions = opts
            # available_options: list[tuple[str, int, int]] = [
            #     (row["name"], row["health"], row["av"]) for row in turn_rows
            # ]
            # availablePassedOptions = [
            #     (op["name"], op["health"], op["av"]) for op in passedOptions
            # ]
            options: list[TurnEntry] = [entries[o.index] for o in opts]
            selected = combatHandler.choose_targets(entries, options, c, m)
            ms.send(CharactersChosen(selected))


def drain(inbox: queue.Queue):
    while True:
        try:
            msg = inbox.get_nowait()
        except queue.Empty:
            return True
        if msg is None:
            return False
        handle(msg)


last_log = ""
turn_rows = []


def say(text: str):
    global last_log
    last_log = text
    terminalDisplay.contextDisplay.print()


inputController.start()

colorama.init(autoreset=True)
utils.clear()
print("\033[?25l", end="")

terminalDisplay.contextDisplay.messageProvider = lambda w, h: (
    utils.boxify(w, h, last_log) if last_log else []
)
terminalDisplay.combatDisplay.messageProvider = lambda w, h: (
    turn_order_lines(turn_rows, w, h) if turn_rows else []
)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("localhost", 63827))
    ms = MessageSocket(s)
    inbox = queue.Queue()
    threading.Thread(target=receiver, args=(ms, inbox), daemon=True).start()
    server_gone = False
    try:
        ms.send(Join([0, 1]))
        while True:
            if not drain(inbox):
                server_gone = True
                break
            key = inputController.getKey()
            if key == Key.esc:
                break
            if key in KEYS:
                ms.send(Move(KEYS[key]))
            time.sleep(0.001)
    finally:
        print("\033[?25h", end="")
        terminalDisplay.moveCursor(0, 26)
    if server_gone:
        print("Server disconnected")
