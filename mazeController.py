from maze import maze, pretty_print, direction, Room
from party import Party
from combatHandler import CombatHandler
import inputController
from pynput.keyboard import Key
from utils import clear

key_to_direction = {
    Key.left: direction.LEFT,
    Key.right: direction.RIGHT,
    Key.up: direction.UP,
    Key.down: direction.DOWN
}

class mazeController:
    def __init__(self, maze: maze, party: Party):
        self.maze = maze
        self.party = party
        self.discovered_rooms = {party.pos}
        inputController.start()

    def move(self, moveDirection: direction):
        newPos = self.party.pos + moveDirection
        if newPos.x < 0 or newPos.x >= 10 or newPos.y < 0 or newPos.y >= 10:
            return
        currentRoom = self.maze[self.party.pos.y][self.party.pos.x]
        assert isinstance(currentRoom, Room)
        newRoom = self.maze[newPos.y][newPos.x]
        if isinstance(newRoom, Room) and currentRoom.has_connection(moveDirection):
            self.discovered_rooms.add(newPos)
            self.party.pos = newPos
            if newRoom.enemies:
                return CombatHandler(self.party.members, newRoom.enemies)
        return None

    def tick(self):
        clear()
        pretty_print(self.maze, self.discovered_rooms, self.party.pos)
        while True:
            key = inputController.getKey()
            # print(key)
            if key in key_to_direction:
                combat_handler = self.move(key_to_direction[key])
                if combat_handler is not None:
                    return combat_handler
                break
        return
        