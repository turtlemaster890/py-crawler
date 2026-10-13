import room
from maze import maze
from party import Party


def save_maze(maze: maze):
    maze_rep: list[list[dict | None]] = []
    for row in maze:
        row_rep: list[dict | None] = []
        for rm in row:
            if isinstance(rm, room.Room):
                room_rep = rm.to_json()
                row_rep.append(room_rep)
            else:
                row_rep.append(None)
        maze_rep.append(row_rep)
    return maze_rep


def load_maze(maze_rep: list[list[dict | None]]) -> maze:
    mz = []
    for row_rep in maze_rep:
        row = []
        for room_rep in row_rep:
            if isinstance(room_rep, dict):
                rm = room.from_json(room_rep)
            else:
                rm = None
            row.append(rm)
        mz.append(row)
    return mz


def save(mz: maze, party: Party):
    return {"maze": save_maze(mz), "party": party.to_json()}


def load(j) -> tuple[maze, Party]:
    return (load_maze(j["maze"]), Party.from_json(j["party"]))
