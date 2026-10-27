import socket
import tempfile
from pathlib import Path
from typing import Any

import saves
from maze import Pos, gen_main_path
from player import Player
from party import Party
from enemy import enemy
from mazeController import mazeController
from netgame import *
from netutil import MessageSocket
import threading
from squad import Squad
import terminalDisplay
from combatHandler import CombatResult
from netcombat import NetworkCombatHandler

saves.SAVE_LOCATION = Path(tempfile.mkdtemp())
saves.save_file = saves.SAVE_LOCATION / "server_save.json"

terminalDisplay.contextDisplay.print_boxify = lambda message: None

START = Pos(14, 6)

party = Party(
    START,
    [
        Player(name="Player1", class_type="warrior"),
        Player(name="Player2", class_type="mage"),
        Player(name="Player3", class_type="rogue"),
        Player(name="Player4", class_type="warrior"),
    ],
)
mz = gen_main_path(START, 50, 28, 13)
controller = mazeController(mz, 28, 13, party)
party.squads.clear()

lock = threading.Lock()
fighting = set()
clients = {}
PAUSE = 0.3


def fight_notify(members: list[Player], msg: dict[str, Any]):
    with lock:
        targets = [
            ms
            for ms, squad in clients.items()
            if squad is not None and any(c in squad.characters for c in members)
        ]
    for ms in targets:
        ms.send_msg(msg)


def make_handler(party: Party, players: list[Player], enemies: list[enemy]):
    members = list(players)
    return NetworkCombatHandler(
        party,
        players,
        enemies,
        notify=lambda msg, members=members: fight_notify(members, msg),
        pause_seconds=PAUSE,
    )


controller.handler_factory = make_handler

handlers: dict[NetworkCombatHandler, list[Squad]] = {}


def run_fight(handler: NetworkCombatHandler, squad: Squad):
    try:
        print("fight started")
        handlers.setdefault(handler, []).append(squad)
        result = handler.combat()
        while result is CombatResult.CONTINUE:
            result = handler.combat()
        print("fight ended:", result.name)
        handler.notify({"type": "combat_end", "result": result.name})
        with lock:
            if result is CombatResult.VICTORY:
                saves.save(mz, party)
            else:
                for c in squad.characters:
                    c.health = c.max_health
                    c.leaveCombat()
                squad.pos = Pos(START.x, START.y)
    finally:
        with lock:
            fighting.discard(squad)
        del handlers[handler]
        broadcast()


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


def serve_client(conn: socket.socket):
    print("a client has connected")
    ms = MessageSocket(conn)
    with lock:
        clients[ms] = None
    try:
        while True:
            msg = ms.recv_msg()
            if msg is None:
                break
            if not isinstance(msg, dict):
                ms.send_msg({"type": "error", "message": "messages must be objects"})
                continue

            reply = None
            changed = False
            fight = None
            with lock:
                msg_type = msg.get("type")
                squad = clients.get(ms)
                if msg_type == "join":
                    if squad is not None:
                        reply = {"type": "error", "message": "you have already joined"}
                    else:
                        new_squad, error = handle_join(party, msg, START)
                        if error is not None:
                            ms.send_msg({"type": "error", "message": error})
                        else:
                            clients[ms] = new_squad
                            changed = True

                elif msg_type == "move":
                    if squad is None:
                        reply = {"type": "error", "message": "join first"}
                    elif squad in fighting:
                        reply = {"type": "error", "message": "you are in a fight"}
                    else:
                        handler, success, _ = apply_message(controller, squad, msg)
                        changed = success
                        if handler is not None:
                            fighting.add(squad)
                            fight = (handler, squad)
                elif msg_type == "option_chosen":
                    if squad is None:
                        reply = {"type": "error", "message": "join first"}
                    elif squad not in fighting:
                        reply = {"type": "error", "message": "you are not in a fight"}
                    else:
                        for handler, squads in handlers.items():
                            if squad in squads:
                                handler.offer_action(squad, msg.get("option", 0))
                else:
                    reply = {"type": "error", "message": "unkown message type"}

            if reply is not None:
                ms.send_msg(reply)
            if fight is not None:
                threading.Thread(target=run_fight, args=fight, daemon=True).start()
            if changed:
                broadcast()
    finally:
        with lock:
            clients.pop(ms, None)
        print("a client has disconnected")
        conn.close()


HOST = "localhost"
PORT = 63827

if __name__ == "__main__":
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
