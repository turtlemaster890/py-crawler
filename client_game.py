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

KEYS = {Key.up:"UP", Key.down:"DOWN", Key.left:"LEFT", Key.right:"RIGHT", Key.enter:"select"}

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
    terminalDisplay.mazeDisplay.messageProvider = (
        lambda w, h: pretty_print_list(w, h, grid, discovered, my_pos)
    )
    
    terminalDisplay.updateDisplays()

inputController.start()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("localhost", 5000))
    ms = MessageSocket(s)
    snap = ms.recv_msg()
    render(snap)
    while True:
        letter = inputController.getKey()
        if letter == 'q':
            break
        if letter in KEYS:


            ms.send_msg({"type": "move", "dir": KEYS[letter]})
            snap = ms.recv_msg()
            if snap is None:
                print("server disconnected")
                break
            render(snap)
        
        else:
            time.sleep(0.01)
        