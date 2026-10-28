from Pos import Pos
from mazeController import mazeController
from packets import Snapshot
from party import Party
from room import Room, str_to_room_type

type_names = {cls: name for name, cls in str_to_room_type.items()}


def handle_join(party: Party, chars: list[int], start_pos: Pos):
    for i in chars:
        if i < 0 or i >= len(party.members):
            return None, f"there is no character number {i}"
    players = [party.members[i] for i in chars]
    try:
        squad = party.create_squad(start_pos, players)
    except ValueError as e:
        return None, str(e)
    return squad, None


def make_snapshot(controller: mazeController, you: int | None = None) -> Snapshot:
    party = controller.party

    squads = []
    for i, squad in enumerate(party.squads):
        squads.append({"index": i, "pos": squad.pos.to_json()})

    rooms = []
    for pos in party.discovered_positions:
        room = controller.maze[pos.y][pos.x]
        if not isinstance(room, Room):
            continue
        rooms.append(
            {
                "pos": pos.to_json(),
                "connections": [c.name for c in room.connections],
                "room_type": type_names.get(type(room), "room"),
                "colour": room.colour,
                "selected_colour": room.selectedColour,
                "description": room.description,
            }
        )

    return Snapshot(
        you,
        controller.width,
        controller.height,
        squads,
        rooms,
    )
