from direction import direction
from maze import maze, pretty_print_list
from Pos import Pos
from party import Party
from combatHandler import CombatHandler
import utils
import inputController
import saves
from pynput.keyboard import Key
from room import Room

# from utils import clear
import terminalDisplay

key_to_direction = {
    Key.left: direction.LEFT,
    Key.right: direction.RIGHT,
    Key.up: direction.UP,
    Key.down: direction.DOWN,
}


class mazeController:
    def __init__(
        self,
        maze: maze,
        width: int,
        height: int,
        party: Party,
        startPos: Pos | None = None,
    ):
        self.maze = maze
        self.width = width
        self.height = height
        self.party = party
        # self.discovered_rooms = {party.pos}

        startPos = startPos or party.pos

        startRoom = maze[startPos.y][startPos.x]
        assert isinstance(startRoom, Room)
        for connection in startRoom.connections:
            self.party.discovered_positions.add(startPos + connection)
        # utils.addPrintFunction("maze", lambda: pretty_print(self.maze, self.discovered_rooms, self.party.pos), 0)
        terminalDisplay.mazeDisplay.messageProvider = lambda x, y: pretty_print_list(
            x, y, self.maze, self.party.discovered_positions, self.party.pos
        )

    def move(self, moveDirection: direction) -> tuple[CombatHandler | None, bool]:
        newPos = self.party.pos + moveDirection
        if (
            newPos.x < 0
            or newPos.x >= self.width
            or newPos.y < 0
            or newPos.y >= self.height
        ):
            return None, False
        currentRoom = self.maze[self.party.pos.y][self.party.pos.x]
        assert isinstance(currentRoom, Room)
        newRoom = self.maze[newPos.y][newPos.x]
        if isinstance(newRoom, Room) and currentRoom.has_connection(moveDirection):
            self.party.discovered_positions.add(newPos)
            for connection in newRoom.connections:
                self.party.discovered_positions.add(newPos + connection)
            self.party.pos = newPos
            # newRoom.enter_room(self.party)
            terminalDisplay.contextDisplay.print_boxify("Autosaving...")
            saves.save(self.maze, self.party)
            if newRoom.enemies:
                return (
                    CombatHandler(self.party, self.party.members, newRoom.enemies),
                    True,
                )
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
            if key == Key.enter:
                self.room_options()
                return
        return

    def room_options(self):
        options = [("View Inventory", self.party.inventory_menu)]
        current_room = self.maze[self.party.pos.y][self.party.pos.x]
        assert isinstance(current_room, Room)
        if current_room.has_action:
            options.append(("Use Room", lambda: current_room.room_action(self.party)))
        selected = 0
        lastProvider = terminalDisplay.contextDisplay.messageProvider
        terminalDisplay.contextDisplay.messageProvider = lambda w, h: show_room_options(
            w, h, [option[0] for option in options], selected
        )

        while True:
            selected %= len(options) + 1
            terminalDisplay.updateDisplays()
            while True:
                key = inputController.getKey()
                if key and key in utils.key_to_delta:
                    selected += utils.key_to_delta[key]
                    break
                if key == Key.enter:
                    if selected < len(options):
                        options[selected][1]()
                        break
                    terminalDisplay.contextDisplay.messageProvider = lastProvider
                    return


def show_room_options(
    w: int, h: int, options: list[str], selected: int = -1
) -> list[str]:
    nameSpace = w - 5
    # longestName = max([len(item[0].name) for item in self.items])
    # additionalChars = max(0, longestName - 8)
    out = []
    out.append("┌" + "─" * (w - 2) + "┐")
    out.append("│" + "Actions".center(w - 2) + "│")
    out.append("├" + "─" * (w - 2) + "┤")
    for i, option in enumerate(options):
        out.append(
            f"│{("> " if i == selected else "  ")}{option[:nameSpace].ljust(nameSpace)} │"
        )
    out.append(
        f"│{("> " if selected == len(options) else "  ")}{"Cancel".ljust(w - 5)} │"
    )
    out.append("└" + "─" * (w - 2) + "┘")
    return out
