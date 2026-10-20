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

def make_snapshot(controller):
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
        "width": controller.width,
        "height": controller.height,
        "squads": squads,
        "rooms": rooms,
    }