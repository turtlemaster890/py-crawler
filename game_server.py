import queue
import socket
import tempfile
from pathlib import Path
import time

from direction import direction
import menuHelper
from packets import (
    CharactersChosen,
    CombatEnd,
    Error,
    Join,
    Log,
    Menu,
    MenuChoice,
    Move,
    OpenActions,
    OptionChosen,
    Packet,
    PacketError,
    Roster,
)
import saves
from maze import Pos, gen_main_path
from player import Player
from party import Party
from enemy import Enemy
from mazeController import mazeController
from netgame import *
from netutil import MessageSocket
import threading
from squad import Squad
import terminalDisplay
from combatHandler import CombatResult
from netcombat import NetworkCombatHandler
import utils


class ClientGone(Exception):
    pass


_ctx = threading.local()

busy: set[Squad] = set()
pending: dict[Squad, queue.Queue] = {}


def _log(text, typed=False):
    h = getattr(_ctx, "handler", None)
    if h is not None:
        h.announce(text, typed)
        return
    ms = getattr(_ctx, "ms", None)
    if ms is not None:
        ms.send(Log(text, typed))


def remote_menu(title, options, back=True):
    ms, squad = _ctx.ms, _ctx.squad
    q = queue.Queue()
    pending[squad] = q
    ms.send(Menu(title, list(options), back))
    while True:
        o = q.get()
        if o is None:
            raise ClientGone
        if (o == -1 and back) or 0 <= o < len(options):
            return o


def roster_packet() -> Roster:
    taken = {c for sq in party.squads for c in sq.characters}
    return Roster(
        [
            {
                "index": i,
                "name": m.name,
                "class_type": m.class_type,
                "available": m not in taken and not in_fight([m]),
            }
            for i, m in enumerate(party.members)
        ]
    )


menuHelper.menu = remote_menu


terminalDisplay.contextDisplay.print_boxify = lambda message: _log(message)
terminalDisplay.contextDisplay.type_print = lambda message, *a, **k: _log(message, True)
utils.wait_for_enter = lambda: (
    time.sleep(PAUSE)
    if getattr(_ctx, "handler", None) or getattr(_ctx, "ms", None)
    else None
)

saves.SAVE_LOCATION = Path(tempfile.mkdtemp())
saves.save_file = saves.SAVE_LOCATION / "server_save.json"

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
clients: dict[MessageSocket, Squad | None] = {}
PAUSE = 1


def fight_notify(members: list[Player], msg: Packet):
    with lock:
        targets = [
            ms
            for ms, squad in clients.items()
            if squad is not None and any(c in squad.characters for c in members)
        ]
    for ms in targets:
        ms.send(msg)


def make_handler(party: Party, players: list[Player], enemies: list[Enemy]):
    existing = room_fights.get(id(enemies))
    if existing is not None:
        fight_members[existing].extend(players)
        existing.add_players(players)
        return existing
    members = list(players)
    handler = NetworkCombatHandler(
        party,
        players,
        enemies,
        notify=lambda msg, members=members: fight_notify(members, msg),
        pause_seconds=PAUSE,
    )
    fight_members[handler] = members
    room_fights[id(enemies)] = handler
    return handler


controller.handler_factory = make_handler

handlers: dict[NetworkCombatHandler, list[Squad]] = {}
fight_members: dict[NetworkCombatHandler, list[Player]] = {}
room_fights: dict[int, NetworkCombatHandler] = {}


def register(handler: NetworkCombatHandler, squad: Squad) -> bool:
    fighting.add(squad)
    squads = handlers.setdefault(handler, [])
    squads.append(squad)
    return len(squads) == 1


def in_fight(chars: list[Player]) -> bool:
    return any(c in h.players or c in h.leaving for h in handlers for c in chars)


def run_fight(handler: NetworkCombatHandler):
    try:
        print("fight started")
        result = handler.combat()
        broadcast()
        while result is CombatResult.CONTINUE:
            result = handler.combat()
            broadcast()
        print("fight ended:", result.name)
        handler.notify(CombatEnd(result.name))
        with lock:
            if result is CombatResult.VICTORY:
                if party.squads:
                    saves.save(mz, party)
            else:
                for squad in handlers.get(handler, []):
                    for c in squad.characters:
                        c.health = c.max_health
                        c.leaveCombat()
                    squad.pos = Pos(START.x, START.y)
    finally:
        with lock:
            for s in handlers.pop(handler, []):
                fighting.discard(s)
            fight_members.pop(handler, None)
            for k, h in list(room_fights.items()):
                if h is handler:
                    del room_fights[k]
        broadcast()


def run_actions(ms: MessageSocket, squad: Squad):
    _ctx.ms, _ctx.squad = ms, squad
    handler = None
    new = False
    try:
        handler = controller.room_options(squad)
        with lock:
            if party.squads:
                saves.save(mz, party)
            if handler is not None and isinstance(handler, NetworkCombatHandler):
                new = register(handler, squad)
    except ClientGone:
        handler = None
    finally:
        _ctx.ms = None
        pending.pop(squad, None)
        with lock:
            busy.discard(squad)
    if handler is None:
        broadcast()
    elif new:
        if isinstance(handler, NetworkCombatHandler):
            run_fight(handler)
    else:
        handler.refresh()


# def snapshot_for(ms):
#     with lock:


def broadcast():
    with lock:
        roster = roster_packet()
        for ms, squad in clients.items():
            if squad is None:
                ms.send(roster)
                continue
            squad_index = party.squads.index(squad)
            ms.send(make_snapshot(controller, squad_index))


def serve_client(conn: socket.socket):
    print("a client has connected")
    ms = MessageSocket(conn)
    with lock:
        clients[ms] = None
        ms.send(roster_packet())
    try:
        while True:
            try:
                pkt = ms.recv()
            except PacketError as e:
                ms.send(Error(str(e)))
                continue
            if pkt is None:
                break

            reply = None
            changed = False
            fight = None
            joined = None
            actions = None
            with lock:
                squad = clients.get(ms)
                match pkt:
                    case Join(characters=chars):
                        if squad is not None:
                            reply = Error("You have already joined")
                        else:
                            new_squad, error = handle_join(party, chars, START)
                            if error is not None:
                                ms.send(Error(error))
                                ms.send(roster_packet())
                            elif in_fight(
                                [
                                    party.members[i]
                                    for i in chars
                                    if 0 <= i < len(party.members)
                                ]
                            ):
                                reply = Error(
                                    "That character is still leaving a fight, try again"
                                )
                            else:
                                clients[ms] = new_squad
                                changed = True

                    case Move(dir=d):
                        if squad is None:
                            reply = Error("Join first")
                        elif squad in fighting or squad in busy:
                            reply = Error("You are in a fight")
                        elif d not in direction.__members__:
                            reply = Error(f"Bad direction {d!r}")
                        else:
                            handler, success, _ = controller.handle_move(
                                direction[d], squad
                            )
                            changed = success
                            if handler is not None and isinstance(
                                handler, NetworkCombatHandler
                            ):
                                if register(handler, squad):
                                    fight = handler
                                else:
                                    joined = handler

                    case OptionChosen(option=o):
                        if squad is None:
                            reply = Error("Join first")
                        elif squad not in fighting:
                            reply = Error("You are not in a fight")
                        else:
                            for handler, squads in handlers.items():
                                if squad in squads:
                                    handler.offer_action(squad, o)
                    case CharactersChosen(selected=sel):
                        if squad is None:
                            reply = Error("Join first")
                        elif squad not in fighting:
                            reply = Error("You are not in a fight")
                        else:
                            for handler, squads in handlers.items():
                                if squad in squads:
                                    handler.offer_selection(squad, sel)
                    case OpenActions():
                        if squad is None:
                            reply = Error("Join first")
                        elif squad in fighting or squad in busy:
                            reply = Error("You are busy")
                        else:
                            busy.add(squad)
                            actions = (ms, squad)
                    case MenuChoice(option=o):
                        if squad is None:
                            reply = Error("Join first")
                        else:
                            q = pending.get(squad)
                            if q is not None and type(o) is int:
                                q.put(o)
                    case _:
                        reply = Error("Unexpected Packet")

            if reply is not None:
                ms.send(reply)
            if fight is not None:
                threading.Thread(target=run_fight, args=(fight,), daemon=True).start()
            if joined is not None:
                joined.refresh()
            if actions is not None:
                threading.Thread(target=run_actions, args=actions, daemon=True).start()
            if changed:
                broadcast()
    finally:
        with lock:
            squad = clients.pop(ms, None)
            if squad is not None:
                for h, sqs in list(handlers.items()):
                    if squad in sqs:
                        sqs.remove(squad)
                        h.remove_players_later(list(squad.characters))
                        for c in squad.characters:
                            if c in fight_members.get(h, []):
                                fight_members[h].remove(c)
                fighting.discard(squad)
                busy.discard(squad)
                q = pending.pop(squad, None)
                if q is not None:
                    q.put(None)
                if squad in party.squads:
                    party.squads.remove(squad)
        print("a client has disconnected")
        conn.close()
        broadcast()


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
