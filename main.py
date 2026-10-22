from maze import Pos, gen_main_path, maze
from direction import direction
from player import Player
from party import Party
import json
import inputController
from combatHandler import CombatHandler
from mazeController import mazeController
import saves
import startMenu
import utils
import colorama

input_to_direction = {
    "u": direction.UP,
    "d": direction.DOWN,
    "l": direction.LEFT,
    "r": direction.RIGHT,
}


combat_handler: CombatHandler | None = None

mz: maze

party: Party


def main():
    global party, mz, combat_handler
    try:
        colorama.init(autoreset=True)
        utils.clear()
        print("\033[?25l", end="")

        saves.select_save_file()

        try:
            with open(saves.save_file, "r") as f:
                save = json.load(f)
                mz, party = saves.load(save)
        except FileNotFoundError, json.JSONDecodeError, KeyError:
            # We do not already have a save file
            plrs = startMenu.pick_players(4)

            party = Party(Pos(14, 6), plrs)
            party.funds = 900
            mz = gen_main_path(party.pos, 50, 28, 13)

        mController = mazeController(mz, 28, 13, party)
        current_room = mz[party.pos.y][party.pos.x]
        if current_room:
            # current_room.enter_room(party)
            if current_room.enemies:
                combat_handler = CombatHandler(
                    party, party.members, current_room.enemies
                )


        while True:
            while combat_handler:
                if not combat_handler.combat():
                    combat_handler = None
                    saves.save(mz, party)
            combat_handler = mController.tick()
    finally:
        print("\033[?25h", end="")


if __name__ == "__main__":
    inputController.start()
    main()
