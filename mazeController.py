import menuHelper
from direction import direction
from maze import maze, pretty_print_list
from Pos import Pos
from party import Party
from combatHandler import CombatHandler
import inputController
import saves
from pynput.keyboard import Key
from room import Room
import utils

# from utils import clear
import terminalDisplay

key_to_direction: dict[Key, direction] = {
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
    ) -> None:
        self.maze = maze
        self.width: int = width
        self.height: int = height
        self.party: Party = party
        # self.discovered_rooms = {party.pos}

        startPos = startPos or party.pos

        startRoom: Room | None = maze[startPos.y][startPos.x]
        assert isinstance(startRoom, Room)
        for connection in startRoom.connections:
            self.party.discovered_positions.add(startPos + connection)
        terminalDisplay.mazeDisplay.messageProvider = lambda x, y: pretty_print_list(
            x, y, self.maze, self.party.discovered_positions, self.party.pos
        )
        terminalDisplay.descriptionDisplay.messageProvider = (
            lambda w, h: self.print_description(w, h)
        )

    def print_description(self, w, h):
        current_room = self.maze[self.party.pos.y][self.party.pos.x]
        assert isinstance(current_room, Room)
        return utils.boxify(
            w,
            h,
            current_room.description
            + (" " if current_room.description else "")
            + "Use [Enter] to open actions.",
        )

    def move(self, moveDirection: direction) -> tuple[CombatHandler | None, bool]:
        newPos: Pos = self.party.pos + moveDirection
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

    def tick(self) -> CombatHandler | None:
        # clear()
        # pretty_print(self.maze, self.discovered_rooms, self.party.pos)
        # utils.printSequences()
        terminalDisplay.updateDisplays()
        while True:
            key: Key | inputController.KeyCode | None = inputController.getKey()
            # print(key)
            if key in key_to_direction:
                combat_handler, success = self.move(key_to_direction[key])
                if not success:
                    continue
                if combat_handler is not None:
                    return combat_handler
                break
            if key == Key.enter:
                r = self.room_options()
                saves.save(self.maze, self.party)
                return r
        return

    def room_options(self):
        options = [("View Inventory", self.party.inventory_menu)]
        current_room: Room | None = self.maze[self.party.pos.y][self.party.pos.x]
        assert isinstance(current_room, Room)
        options.extend(
            [
                (action[0], lambda: action[1](self.party))
                for action in current_room.room_actions
            ]
        )
        while True:
            option = menuHelper.menu("Actions", [option[0] for option in options])
            if option is not None:
                return options[option][1]()
            else:
                return

    # def room_options(self) -> None:
    #     options: list[tuple[str, Callable[[], None]]] = [("View Inventory", self.party.inventory_menu)]
    #     current_room: Room | None = self.maze[self.party.pos.y][self.party.pos.x]
    #     assert isinstance(current_room, Room)
    #     options.extend([(action[0], lambda: action[1](self.party)) for action in current_room.room_actions])
    #     selected = 0
    #     lastProvider: Callable[[int, int], list[str]] | None = terminalDisplay.contextDisplay.messageProvider
    #     terminalDisplay.contextDisplay.messageProvider = lambda w, h: show_room_options(
    #         w, h, [option[0] for option in options], selected
    #     )

    #     while True:
    #         selected %= len(options) + 1
    #         terminalDisplay.updateDisplays()
    #         while True:
    #             key: Key | inputController.KeyCode | None = inputController.getKey()
    #             if key and key in utils.key_to_delta:
    #                 selected += utils.key_to_delta[key]
    #                 break
    #             if key == Key.enter:
    #                 if selected < len(options):
    #                     options[selected][1]()
    #                     break
    #                 terminalDisplay.contextDisplay.messageProvider = lastProvider
    #                 return


def show_room_options(
    w: int, h: int, options: list[str], selected: int = -1
) -> list[str]:
    nameSpace: int = w - 5
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
