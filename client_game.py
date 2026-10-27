import socket
from typing import Any
import menuHelper
from netutil import MessageSocket
from direction import direction
from maze import pretty_print_list
from Pos import Pos
from room import Room
import terminalDisplay
import inputController
from pynput.keyboard import Key
import time
import utils
import colorama
import queue
import threading

KEYS = {Key.up: "UP", Key.down: "DOWN", Key.left: "LEFT", Key.right: "RIGHT"}


def turn_order_lines(rows: list[dict], w: int, h: int):
    out = []
    name_space = w - 13
    out.append("┌" + "─" * (w - 2) + "┐")
    out.append("│" + "TURN ORDER".center(w - 2) + "│")
    out.append("├" + "─" * (w - 2) + "┤")
    for row in rows:
        name = f'{row["name"]} ({row["health"]}♥)'[:name_space].ljust(name_space)
        out.append(f"│ {name} │ {row['av']:<3} AV │")
    out.append("└" + "─" * (w - 2) + "┘")
    return out


def build_view(snap: dict):
    width, height = snap["width"], snap["height"]

    grid: list[list[Room | None]] = [
        [None for _ in range(width)] for _ in range(height)
    ]
    discovered = set()

    for entry in snap["rooms"]:
        pos = Pos.from_json(entry["pos"])
        dirs = {direction[name] for name in entry["connections"]}

        room = Room(dirs)
        room.colour = entry["colour"]
        room.selectedColour = entry["selected_colour"]
        room.description = entry["description"]

        grid[pos.y][pos.x] = room
        discovered.add(pos)

    my_pos = Pos.from_json(snap["squads"][snap["you"]]["pos"])

    return grid, discovered, my_pos


def render(snap: dict):
    grid, discovered, my_pos = build_view(snap)
    here = grid[my_pos.y][my_pos.x]
    description = here.description if here is not None else ""
    terminalDisplay.mazeDisplay.messageProvider = lambda w, h: pretty_print_list(
        w, h, grid, discovered, my_pos
    )
    terminalDisplay.descriptionDisplay.messageProvider = lambda w, h: utils.boxify(
        w, h, description
    )

    terminalDisplay.updateDisplays()


def receiver(ms: MessageSocket, inbox: queue.Queue):
    try:
        while True:
            msg = ms.recv_msg()
            inbox.put(msg)
            if msg is None:
                return
    finally:
        inbox.put(None)


def handle(msg: Any):
    if isinstance(msg, dict):
        global turn_rows
        kind = msg.get("type")
        if kind == "snapshot":
            render(msg)
        elif kind == "error":
            say(msg.get("message", "error"))
        elif kind == "log":
            say(msg.get("text", ""))
        elif kind == "combat_state":
            turn_rows = msg.get("turn_order", [])
            terminalDisplay.combatDisplay.print()
        elif kind == "combat_end":
            turn_rows = []
            terminalDisplay.combatDisplay.print()
            say(msg.get("result", ""))
        elif kind == "choose_option":
            if len(msg["options"]) < 1:
                return
            option = menuHelper.menu("Choose option", msg["options"], False)
            ms.send_msg({"type": "option_chosen", "option": option})


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
        ms.send_msg({"type": "join", "characters": [1]})
        while True:
            if not drain(inbox):
                server_gone = True
                break
            key = inputController.getKey()
            if key == Key.esc:
                break
            if key in KEYS:
                ms.send_msg({"type": "move", "dir": KEYS[key]})
            time.sleep(0.001)
    finally:
        print("\033[?25h", end="")
        terminalDisplay.moveCursor(0, 26)
    if server_gone:
        print("Server disconnected")
