from enum import Enum
import random

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

colorama_init()

add_up = {
    "·": "╵",
    "╴": "┘",
    "╶": "└",
    "╷": "│",
    "─": "┴",
    "┐": "┤",
    "┌": "├",
    "┬": "┼"
}

add_down = {
    "·": "╷",
    "╴": "┐",
    "╶": "┌",
    "╵": "│",
    "─": "┬",
    "┘": "┤",
    "└": "├",
    "┴": "┼"
}

add_left = {
    "·": "╴",
    "╶": "─",
    "╵": "┘",
    "╷": "┐",
    "│": "┤",
    "└": "┴",
    "┌": "┬",
    "├": "┼"
}

add_right = {
    "·": "╶",
    "╴": "─",
    "╵": "└",
    "╷": "┌",
    "│": "├",
    "┘": "┴",
    "┐": "┬",
    "┤": "┼"
}

def connections_to_char(connections: set[direction]):
    c = "·"
    for d in list(connections):
        if d == direction.UP: c = add_up[c]
        if d == direction.DOWN: c = add_down[c]
        if d == direction.LEFT: c = add_left[c]
        if d == direction.RIGHT: c = add_right[c]
    return c

class Pos:
    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y

    def __add__(self, other) -> Pos:
        if isinstance(other, Pos):
            return Pos(self.x + other.x, self.y + other.y)
        if isinstance(other, direction):
            return Pos(self.x + other.value[0], self.y + other.value[1])
        return NotImplemented

def pretty_print(maze: list[list[Room | None]]):
    for row in maze:
        for r in row:
            if not isinstance(r, Room):
                print(" ", end="")
            else:
                print(r.colour + connections_to_char(r.connections), end = "")
        print()

# step 1: generate path to boss room
def gen_main_path(startPos: Pos, maxSteps: int):
    maze: list[list[Room | None]] = []
    for _ in range(10):
        maze.append([None] * 10)
    currentPos = startPos
    maze[currentPos.y][currentPos.x] = StartRoom()
    i = 0
    while True:
        i += 1
        # move in random direction
        moveDirection = random.choice(list(direction))
        newPos = currentPos + moveDirection
        if newPos.x < 0 or newPos.x >= 10 or newPos.y < 0 or newPos.y >= 10:
            continue
        if maze[newPos.y][newPos.x] is None:
            # make connections between rooms
            maze[newPos.y][newPos.x] = Room(connections={moveDirection.opposite()})
            currentRoom = maze[currentPos.y][currentPos.x]
            assert isinstance(currentRoom, Room)
            currentRoom.make_connection(moveDirection)
            currentPos = newPos
        else:
            if i > 10:
                maze[currentPos.y][currentPos.x] = EndRoom(maze[currentPos.y][currentPos.x].connections)
                return maze
            continue

        # hard cap length
        if i >= maxSteps:
            maze[currentPos.y][currentPos.x] = EndRoom(maze[currentPos.y][currentPos.x].connections)
            return maze

        # # random length - shorter more often
        # if random.random() > 1 - (i / maxSteps):
        #     return maze





def gen_branch(maze, pos, dir):
    ...

def generate_maze(width: int, height: int):
    ...

class direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def opposite(self):
        return {
            direction.UP: direction.DOWN,
            direction.DOWN: direction.UP,
            direction.LEFT: direction.RIGHT,
            direction.RIGHT: direction.LEFT
        }[self]


class Room:
    def __init__(self, connections: set[direction] | None = None):
        if connections is None:
            connections = set()
        self.connections = connections
        self.colour = Fore.WHITE

    def has_connection(self, direction: direction):
        return direction in self.connections

    def make_connection(self, direction: direction):
        self.connections.add(direction)

    def __repr__(self):
        return f"R({[d.name for d in self.connections]})"

class StartRoom(Room):
    def __init__(self, connections: set[direction] | None = None):
        super().__init__(connections)
        self.colour = Fore.LIGHTGREEN_EX

class EndRoom(Room):
    def __init__(self, connections: set[direction] | None = None):
        super().__init__(connections)
        self.colour = Fore.LIGHTRED_EX


class Maze:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.maze = []
        for _ in range(height):
            self.maze.append([0] * width)