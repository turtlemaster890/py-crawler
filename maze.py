from enum import Enum
import random
import enemy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from party import Party

# from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

# colorama_init()

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

type maze = list[list[Room | None]]

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

    def __str__(self):
        return f"P({self.x}, {self.y})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Pos):
            return self.x == other.x and self.y == other.y
        return False

    def __key(self):
        return (self.x, self.y)

    def __hash__(self):
        return hash(self.__key())


def pretty_print(maze: maze, discovered_positions: set[Pos], current_position: Pos):
    for y, row in enumerate(maze):
        for x, r in enumerate(row):
            if not isinstance(r, Room) or Pos(x, y) not in discovered_positions:
                print(" ", end=Style.RESET_ALL)
            else:
                print((r.selectedColour if current_position == Pos(x, y) else (Style.DIM + r.colour)) + connections_to_char(r.connections), end = Style.RESET_ALL)
        print()

def pretty_print_list(w: int, h: int, maze: maze, discovered_positions: set[Pos], current_position: Pos) -> list[str]:
    content_width = w - 2
    content_height = h - 2

    out = ["┌" + "─" * content_width + "┐"]
    for y in range(content_height):
        if y < len(maze):
            row = maze[y]
            line_chars = []
            for x in range(content_width):
                if x < len(row):
                    r = row[x]
                    if not isinstance(r, Room) or Pos(x, y) not in discovered_positions:
                        line_chars.append(" ")
                    else:
                        colour = r.selectedColour if current_position == Pos(x, y) else (Style.DIM + r.colour)
                        char = connections_to_char(r.connections)
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
def gen_main_path(startPos: Pos, maxSteps: int, x: int, y: int):
    maze: list[list[Room | None]] = []
    for _ in range(y):
        maze.append([None] * x)
    currentPos = startPos
    maze[currentPos.y][currentPos.x] = StartRoom()
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
                maze[newPos.y][newPos.x] = Room(connections={moveDirection.opposite()})
                assert isinstance(currentRoom, Room)
                currentRoom.make_connection(moveDirection)
                currentPos = newPos
                branch_positions.append(currentPos)
            else:
                options.remove(moveDirection)
                break

    currentRoom = maze[currentPos.y][currentPos.x]
    assert isinstance(currentRoom, Room)
    maze[currentPos.y][currentPos.x] = EndRoom(currentRoom.connections)
    if currentPos in branch_positions:
        branch_positions.remove(currentPos)
    return gen_branches(maze, branch_positions, x, y, 12)


def gen_branches(maze: maze, positions: list[Pos], width: int, height: int, maxBranches: int, d = 1) -> maze:
    options = random.choices(positions, k = maxBranches)
    for pos in options:
        maze = gen_branch(maze, pos, width, height, 9, d)
    return maze
        


def gen_branch(maze: maze, pos: Pos, width: int, height: int, maxBranchLength: int, d: int = 3):
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
                if newPos.x < 0 or newPos.x >= width or newPos.y < 0 or newPos.y >= height:
                        options.remove(moveDirection)
                        continue
                if maze[newPos.y][newPos.x] is None:
                    maze[newPos.y][newPos.x] = Room(connections={moveDirection.opposite()})
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
    def __init__(self, connections: set[direction] | None = None, enemies: list[enemy.enemy] | None = None):
        if connections is None:
            connections = set()
        if enemies is None:
            enemies = []
        self.connections = connections
        self.enemies = enemies
        self.colour = Fore.LIGHTBLACK_EX
        self.selectedColour = Fore.WHITE

    def enter_room(self, party: Party):
        pass

    def has_connection(self, direction: direction):
        return direction in self.connections

    def make_connection(self, direction: direction):
        self.connections.add(direction)

    def __repr__(self):
        return f"R({[d.name for d in self.connections]})"

class StartRoom(Room):
    def __init__(self, connections: set[direction] | None = None):
        super().__init__(connections)
        self.enemies = []
        self.colour = Fore.GREEN
        self.selectedColour = Fore.LIGHTGREEN_EX

class EndRoom(Room):
    def __init__(self, connections: set[direction] | None = None):
        super().__init__(connections, enemies=[enemy.Goblin(name="Super Scary Bob AAA")])
        self.colour = Fore.RED
        self.selectedColour = Fore.LIGHTRED_EX

class ShopRoom(Room):
    def __init__(self, connections: set[direction] | None = None):
        super().__init__(connections)
        self.enemies = []
        self.colour = Fore.YELLOW
        self.selectedColour = Fore.LIGHTYELLOW_EX

    def enter_room(self, party: Party):
        super().enter_room(party)



class Maze:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.maze = []
        for _ in range(height):
            self.maze.append([0] * width)