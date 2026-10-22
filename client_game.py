import socket
from netutil import MessageSocket
from direction import direction
from maze import connections_to_char, pretty_print_list
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

KEYS = {Key.up:"UP", Key.down:"DOWN", Key.left:"LEFT", Key.right:"RIGHT"}

def build_view(snap):
    width, height = snap["width"], snap["height"]

    grid = [[None for _ in range(width)] for _ in range(height)]
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

    my_pos = Pos.from_json(snap["squads"][0]["pos"])

    return grid, discovered, my_pos

def render(snap):
    grid, discovered, my_pos = build_view(snap)
    here = grid[my_pos.y][my_pos.x]
    description = here.description if here is not None else ""
    terminalDisplay.mazeDisplay.messageProvider = (
        lambda w, h: pretty_print_list(w, h, grid, discovered, my_pos)
    )
    terminalDisplay.descriptionDisplay.messageProvider = (
        lambda w, h: utils.boxify(w, h, description)
    )
    
    terminalDisplay.updateDisplays()

def receiver(ms, inbox):
    try:
        while True:
            msg = ms.recv_msg()
            inbox.put(msg)
            if msg is None:
                return
    finally:
        inbox.put(None)

def handle(msg):
    if not isinstance(msg, dict):
        kind = msg.get("type")
        if kind == "snapshot":
            render(msg)
        elif kind == "error":
            terminalDisplay.contextDisplay.print_boxify(msg.get("message", "error"))

def drain(inbox):
    while True:
        try:
            msg = inbox.get_nowait()
        except queue.Empty:
            return True
        if msg is None:
            return False
        handle(msg)

inputController.start()

colorama.init(autoreset=True)
utils.clear()
print("\033[?25l", end="")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("localhost", 5000))
    ms = MessageSocket(s)
    inbox = queue.Queue()
    threading.Thread(target=receiver, args=(ms, inbox), daemon=True).start()
    colorama.init(autoreset=True)
    utils.clear()
    print("\033[?25l", end="")
    server_gone = False
    try:
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
        print("\033[?25l", end="")
        terminalDisplay.moveCursor(0, 26)
    if server_gone:
        print("Server disconnected")