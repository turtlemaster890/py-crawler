from direction import direction
from room import Room, str_to_room_type

type_names = {cls: name for name, cls in str_to_room_type.items()}

def apply_message(controller, squad, msg):
    failure = (None, False, squad)

    if not isinstance(msg, dict):
        return failure

    msg_type = msg.get("type")

    if msg_type == "move":
        name = msg.get("dir")
        if not isinstance(name, str):
            return failure
        try:
            move_dir = direction[name]
        except KeyError:
            return failure
        return controller.handle_move(move_dir, squad)

    return failure

def handle_join(party, msg, start_pos):
    if not isinstance(msg, dict):
        return None, "join message must be an object"

    indexes = msg.get("characters")
    if not isinstance(indexes, list):
        return None, "characters must be a list"

    for i in indexes:
        if type(i) is not int:
            return None, "character numbers must be whole numbers"
        if i < 0 or i >= len(party.members):
            return None, f"there is no character number {i}"
    players = [party.members[i] for i in indexes]
    try:
        squad = party.create_squad(start_pos, players)
    except ValueError as e:
        return None, str(e)
    return squad, None

def make_snapshot(controller, you=None):
    party = controller.party

    squads = []
    for i, squad in enumerate(party.squads):
        squads.append({"index": i, "pos": squad.pos.to_json()})

    rooms = []
    for pos in party.discovered_positions:
        room = controller.maze[pos.y][pos.x]
        if not isinstance(room, Room):
            continue
        rooms.append({
            "pos": pos.to_json(),
            "connections": [c.name for c in room.connections],
            "room_type": type_names.get(type(room), "room"),
            "colour": room.colour,
            "selected_colour": room.selectedColour,
            "description": room.description
        })

    return {
        "type": "snapshot",
        "you": you,
        "width": controller.width,
        "height": controller.height,
        "squads": squads,
        "rooms": rooms,
    }