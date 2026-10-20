import json
import tempfile
from collections import Counter
from pathlib import Path

import saves

# IMPORTANT: redirect saving so the test can't overwrite your real save file
saves.SAVE_LOCATION = Path(tempfile.mkdtemp())
saves.save_file = saves.SAVE_LOCATION / "test_save.json"

from maze import Pos, gen_main_path
from player import Player
from party import Party
from mazeController import mazeController
from room import Room, str_to_room_type
from netgame import apply_message, make_snapshot, type_names

party = Party(
    Pos(14, 6),
    [
        Player(name="Player1", class_type="warrior"),
        Player(name="Player2", class_type="mage"),
    ],
)
mz = gen_main_path(party.squads[0].pos, 50, 28, 13)
controller = mazeController(mz, 28, 13, party)
squad = party.squads[0]


def check(label, condition):
    print(("PASS" if condition else "FAIL"), "-", label)


def describe(label, snap):
    text = json.dumps(snap)  # raises TypeError if something isn't JSON-safe
    json.loads(text)         # and it must survive the trip back
    print(f"--- {label} ---")
    print("size:", len(text), "characters")
    print("maze size:", snap["width"], "x", snap["height"])
    print("squads:", snap["squads"])
    print("room count:", len(snap["rooms"]))
    for r in sorted(snap["rooms"], key=lambda r: r["pos"]):
        # repr() so colour escape codes show as text instead of colouring the terminal
        print(
            "  room", r["pos"], r["connections"],
            "| type:", r.get("room_type", "MISSING"),
            "| colour:", repr(r.get("colour", "MISSING")),
            "| desc:", repr(r.get("description", "MISSING")),
        )


def check_rooms(snap):
    """Every room entry must have the fields the client needs."""
    needed = ["pos", "connections", "colour", "selected_colour", "room_type", "description"]
    for key in needed:
        check(f"every room has '{key}'", all(key in r for r in snap["rooms"]))

    # the room we start on must be reported as the start room
    start = [r for r in snap["rooms"] if r["pos"] == snap["squads"][0]["pos"]
             or tuple(r["pos"]) == tuple(snap["squads"][0]["pos"])]
    check("room under squad 0 has type 'start'",
          bool(start) and start[0].get("room_type") == "start")

    # descriptions in the snapshot must match the real rooms
    ok = True
    for r in snap["rooms"]:
        x, y = r["pos"]
        real = controller.maze[y][x]
        if r.get("description") != real.description:
            ok = False
    check("descriptions match the real rooms", ok)


# --- before moving ---
before = make_snapshot(controller)
describe("before moving", before)
check_rooms(before)

# --- round-trip check over the WHOLE maze (not just discovered rooms) ---
print()
counts = Counter()
round_trip_ok = True
for row in controller.maze:
    for r in row:
        if r is None:
            continue
        name = type_names.get(type(r))
        counts[name] += 1
        if name is None or str_to_room_type[name] is not type(r):
            round_trip_ok = False
check("every room class maps to a name and back", round_trip_ok)
print("room types in this maze:", dict(counts))

# --- move once and compare ---
moved = None
for d in ["UP", "DOWN", "LEFT", "RIGHT"]:
    combat, success, _ = apply_message(controller, squad, {"type": "move", "dir": d})
    if success:
        moved = d
        break
print()
print("moved:", moved)

after = make_snapshot(controller)
describe("after moving", after)
check_rooms(after)

before_rooms = {tuple(r["pos"]) for r in before["rooms"]}
after_rooms = {tuple(r["pos"]) for r in after["rooms"]}
print()
print("squad position before:", before["squads"][0]["pos"])
print("squad position after: ", after["squads"][0]["pos"])
print("newly discovered rooms:", sorted(after_rooms - before_rooms))
check("no rooms disappeared", not (before_rooms - after_rooms))