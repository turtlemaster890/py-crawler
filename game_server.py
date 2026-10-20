import socket
import tempfile
from pathlib import Path

import saves
from maze import Pos, gen_main_path
from player import Player
from party import Party
from mazeController import mazeController
from netgame import apply_message, make_snapshot
from netutil import MessageSocket

saves.SAVE_LOCATION = Path(tempfile.mkdtemp())
saves.save_file = saves.SAVE_LOCATION / "server_save.json"

party = Party(Pos(14, 6), [
    Player(name="Player1", class_type="warrior"),
    Player(name="Player2", class_type="mage")
])
mz = gen_main_path(party.squads[0].pos, 50, 28, 13)
controller = mazeController(mz, 28, 13, party)
squad = party.squads[0]

HOST = "localhost"
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("waiting for a client...")
    conn, addr = s.accept()
    print("client found")
    ms = MessageSocket(conn)
    ms.send_msg(make_snapshot(controller))
    while True:
        msg = ms.recv_msg()
        if msg is None:
            print("client disconnected")
            break
        combat, success, _ = apply_message(controller, squad, msg)
        if combat:
            print("combat")
        ms.send_msg(make_snapshot(controller))