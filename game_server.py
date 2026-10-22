import socket
import tempfile
from pathlib import Path

import saves
from maze import Pos, gen_main_path
from player import Player
from party import Party
from mazeController import mazeController
from netgame import *
from netutil import MessageSocket
import threading
import terminalDisplay

saves.SAVE_LOCATION = Path(tempfile.mkdtemp())
saves.save_file = saves.SAVE_LOCATION / "server_save.json"

terminalDisplay.contextDisplay.print_boxify = lambda message: None

START = Pos(14, 6)

party = Party(START, [
    Player(name="Player1", class_type="warrior"),
    Player(name="Player2", class_type="mage"),
    Player(name="Player3", class_type="rogue"),
    Player(name="Player4", class_type="warrior"),
])
mz = gen_main_path(START, 50, 28, 13)
controller = mazeController(mz, 28, 13, party)
party.squads.clear()

lock = threading.Lock()
clients = {}

# def snapshot_for(ms):
#     with lock:

def broadcast():
    with lock:
        for ms, squad in clients.items():
            if squad is None:
                continue
            squad_index = party.squads.index(squad)
            snapshot = make_snapshot(controller, squad_index)
            ms.send_msg(snapshot)
            

def serve_client(conn):
    print("a client has connected")
    ms = MessageSocket(conn)
    with lock:
        clients[ms] = None
    try:
        while True:
            msg = ms.recv_msg()
            if msg is None:
                break

            with lock:
                msg_type = msg.get("type")
                if msg_type == "join":
                    squad, error = handle_join(party, msg, START)
                    if error is None:
                        clients[ms] = squad
                    else:
                        ms.send_msg({"type":"error", "message":error})
                elif msg_type == "move":
                    squad = clients[ms]
                    if squad is not None:
                        handler, success, squad = apply_message(controller, squad, msg)
                        clients[ms] = squad
                        

            broadcast()
    finally:
        with lock:
            clients.pop(ms, None)
        print("a client has disconnected")
        conn.close()

HOST = "localhost"
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    s.settimeout(1.0)
    print(f"listening on {HOST}:{PORT}")
    while True:
        try:
            conn, addr = s.accept()
        except TimeoutError:
            continue
        conn.settimeout(None)
        threading.Thread(target=serve_client, args=(conn,), daemon=True).start()