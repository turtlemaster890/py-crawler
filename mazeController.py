from maze import maze, pretty_print, pretty_print_list, direction, Room, Pos
from party import Party
from combatHandler import CombatHandler
import inputController
from pynput.keyboard import Key
# from utils import clear
import terminalDisplay
import utils

key_to_direction = {
    Key.left: direction.LEFT,
    Key.right: direction.RIGHT,
    Key.up: direction.UP,
    Key.down: direction.DOWN
}

class mazeController:
    def __init__(self, maze: maze, width: int, height: int, party: Party, startPos: Pos | None = None):
        self.maze = maze
        self.width = width
        self.height = height
        self.party = party
        self.discovered_rooms = {party.pos}

        startPos = startPos or party.pos

        startRoom = maze[startPos.y][startPos.x]
        assert isinstance(startRoom, Room)
        for connection in startRoom.connections:
            self.discovered_rooms.add(startPos + connection)
        inputController.start()
        # utils.addPrintFunction("maze", lambda: pretty_print(self.maze, self.discovered_rooms, self.party.pos), 0)
        terminalDisplay.mazeDisplay.messageProvider = lambda x, y: pretty_print_list(x, y, self.maze, self.discovered_rooms, self.party.pos)

    def move(self, moveDirection: direction) -> tuple[CombatHandler | None, bool]:
        newPos = self.party.pos + moveDirection
        if newPos.x < 0 or newPos.x >= self.width or newPos.y < 0 or newPos.y >= self.height:
            return None, False
        currentRoom = self.maze[self.party.pos.y][self.party.pos.x]
        assert isinstance(currentRoom, Room)
        newRoom = self.maze[newPos.y][newPos.x]
        if isinstance(newRoom, Room) and currentRoom.has_connection(moveDirection):
            self.discovered_rooms.add(newPos)
            for connection in newRoom.connections:
                self.discovered_rooms.add(newPos + connection)
            self.party.pos = newPos
            if newRoom.enemies:
                return CombatHandler(self.party, self.party.members, newRoom.enemies), True
            return None, True
        return None, False

    def tick(self):
        # clear()
        # pretty_print(self.maze, self.discovered_rooms, self.party.pos)
        # utils.printSequences()
        terminalDisplay.updateDisplays()
        while True:
            key = inputController.getKey()
            # print(key)
            if key in key_to_direction:
                combat_handler, success = self.move(key_to_direction[key])
                if not success:
                    continue
                if combat_handler is not None:
                    return combat_handler
                break
        return
        