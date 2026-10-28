from direction import direction
from encounters import bossEncounterFactory, encounterFactory
import random
import utils
from Pos import Pos
from room import Room, StartRoom, EndRoom, ShopRoom, ChestRoom, LockedRoom
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from party import Party

# from colorama import init as colorama_init
from colorama import Fore, Style

# colorama_init()

room_weights: dict[type[Room], int] = {
    Room: 15,
    ChestRoom: 2,
    ShopRoom: 1,
}

branch_room_weights: dict[type[Room], int] = {
    Room: 10,
    ChestRoom: 4,
    ShopRoom: 2,
    LockedRoom: 1,
}

add_up = {
    "·": "╵",
    "╴": "┘",
    "╶": "└",
    "╷": "│",
    "─": "┴",
    "┐": "┤",
    "┌": "├",
    "┬": "┼",
}

add_down = {
    "·": "╷",
    "╴": "┐",
    "╶": "┌",
    "╵": "│",
    "─": "┬",
    "┘": "┤",
    "└": "├",
    "┴": "┼",
}

add_left = {
    "·": "╴",
    "╶": "─",
    "╵": "┘",
    "╷": "┐",
    "│": "┤",
    "└": "┴",
    "┌": "┬",
    "├": "┼",
}

add_right = {
    "·": "╶",
    "╴": "─",
    "╵": "└",
    "╷": "┌",
    "│": "├",
    "┘": "┴",
    "┐": "┬",
    "┤": "┼",
}


def connections_to_char(connections: set[direction]):
    c = "·"
    for d in list(connections):
        if d == direction.UP:
            c = add_up[c]
        if d == direction.DOWN:
            c = add_down[c]
        if d == direction.LEFT:
            c = add_left[c]
        if d == direction.RIGHT:
            c = add_right[c]
    return c


type maze = list[list[Room | None]]


def pretty_print(maze: maze, discovered_positions: set[Pos], current_position: Pos):
    for y, row in enumerate(maze):
        for x, r in enumerate(row):
            if not isinstance(r, Room) or (
                not Pos(x, y) in discovered_positions and not utils.DEBUG_VIEW
            ):
                print(" ", end=Style.RESET_ALL)
            else:
                print(
                    (
                        r.selectedColour
                        if current_position == Pos(x, y)
                        else (Style.DIM + r.colour)
                    )
                    + connections_to_char(r.connections),
                    end=Style.RESET_ALL,
                )
        print()


def pretty_print_list(
    w: int,
    h: int,
    maze: maze,
    discovered_positions: set[Pos],
    current_position: Pos,
    floor: int = 1,
    others: set[Pos] | None = None,
) -> list[str]:
    content_width = w - 2
    content_height = h - 2

    out = ["┌" + f" Floor {floor} ".center(content_width, "─") + "┐"]
    for y in range(content_height):
        if y < len(maze):
            row = maze[y]
            line_chars = []
            for x in range(content_width):
                if x < len(row):
                    r = row[x]
                    if not isinstance(r, Room) or (
                        not Pos(x, y) in discovered_positions and not utils.DEBUG_VIEW
                    ):
                        line_chars.append(" ")
                    else:
                        if current_position == Pos(x, y):
                            colour = r.selectedColour
                        elif others and Pos(x, y) in others:
                            colour = Fore.LIGHTCYAN_EX
                        else:
                            colour = Style.DIM + r.colour
                        char = connections_to_char(r.list_connections())
                        line_chars.append(f"{colour}{char}{Style.RESET_ALL}")
                else:
                    line_chars.append(" ")
            row_str = "".join(line_chars)
        else:
            row_str = " " * content_width

        out.append(f"│{row_str}│")

    out.append("└" + "─" * content_width + "┘")
    return out


# step 1: generate path to boss room
def gen_main_path(startPos: Pos, maxSteps: int, x: int, y: int, floor: int = 1):
    maze: list[list[Room | None]] = []
    for _ in range(y):
        maze.append([None] * x)
    currentPos = startPos
    maze[currentPos.y][currentPos.x] = StartRoom(currentPos)
    branch_positions: list[Pos] = []
    # i = 0
    done = False
    for i in range(maxSteps):
        if done:
            break
        options = list(direction)
        while True:
            # i += 1
            # move in random direction
            if len(options) <= 0:
                done = True
                break
            moveDirection = random.choice(options)
            newPos = currentPos + moveDirection
            if newPos.x < 0 or newPos.x >= x or newPos.y < 0 or newPos.y >= y:
                continue
            currentRoom = maze[currentPos.y][currentPos.x]
            if maze[newPos.y][newPos.x] is None:
                # make connections between rooms
                maze[newPos.y][newPos.x] = random.choices(
                    list(room_weights.keys()), list(room_weights.values()), k=1
                )[0](
                    newPos,
                    connections={moveDirection.opposite()},
                    enemies=encounterFactory(),
                )
                assert isinstance(currentRoom, Room)
                currentRoom.make_connection(moveDirection)
                currentPos = newPos
                branch_positions.append(currentPos)
            else:
                options.remove(moveDirection)
                break

    currentRoom = maze[currentPos.y][currentPos.x]
    assert isinstance(currentRoom, Room)
    maze[currentPos.y][currentPos.x] = EndRoom(
        currentPos, currentRoom.connections, bossEncounterFactory(floor)
    )
    if currentPos in branch_positions:
        branch_positions.remove(currentPos)
    maze = gen_branches(maze, branch_positions, x, y, 12)
    # open_room_spots = [
    #     (x, y)
    #     for y in range(len(maze))
    #     for x in range(len(maze[y]))
    #     if type(maze[y][x]) == Room
    # ]
    # shopRoomSpot = random.choice(open_room_spots)
    # shopRoomSpotRoom = maze[shopRoomSpot[1]][shopRoomSpot[0]]
    # assert isinstance(shopRoomSpotRoom, Room)
    # maze[shopRoomSpot[1]][shopRoomSpot[0]] = ShopRoom(shopRoomSpotRoom.connections)
    if floor > 1:
        for row in maze:
            for rm in row:
                if type(rm) is Room:
                    rm.enemies = encounterFactory(floor)
                if isinstance(rm, Room):
                    for e in rm.enemies:
                        e.scale(floor)
    return maze


def gen_branches(
    maze: maze, positions: list[Pos], width: int, height: int, maxBranches: int, d=1
) -> maze:
    options = random.choices(positions, k=maxBranches)
    for pos in options:
        maze = gen_branch(maze, pos, width, height, 9, d)
    return maze


def gen_branch(
    maze: maze, pos: Pos, width: int, height: int, maxBranchLength: int, d: int = 3
):
    # if d > 3:
    #     return maze
    currentPos = pos
    branchOptions: list[Pos] = []
    for i in range(maxBranchLength):
        options = list(direction)
        while True:
            if len(options) > 0:
                moveDirection = random.choice(options)
                newPos = currentPos + moveDirection
                if (
                    newPos.x < 0
                    or newPos.x >= width
                    or newPos.y < 0
                    or newPos.y >= height
                ):
                    options.remove(moveDirection)
                    continue
                if maze[newPos.y][newPos.x] is None:
                    maze[newPos.y][newPos.x] = maze[newPos.y][
                        newPos.x
                    ] = random.choices(
                        list(branch_room_weights.keys()),
                        list(branch_room_weights.values()),
                        k=1,
                    )[
                        0
                    ](
                        newPos,
                        connections={moveDirection.opposite()},
                        enemies=encounterFactory(),
                    )
                    currentRoom = maze[currentPos.y][currentPos.x]
                    assert isinstance(currentRoom, Room)
                    currentRoom.make_connection(moveDirection)
                    maze[currentPos.y][currentPos.x] = currentRoom
                    currentPos = newPos
                    branchOptions.append(currentPos)
                    break
                else:
                    options.remove(moveDirection)
            else:
                if branchOptions:
                    return gen_branches(maze, branchOptions, width, height, 2, d + 1)
                return maze
    if branchOptions:
        return gen_branches(maze, branchOptions, width, height, 2, d + 1)
    return maze


def generate_maze(width: int, height: int): ...
