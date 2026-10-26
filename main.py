from maze import Pos, gen_main_path, maze
from direction import direction
from player import Player
from party import Party
import json
import inputController
from combatHandler import CombatHandler, CombatResult
from mazeController import mazeController
import saves
import utils
import colorama
import sys

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
            player1 = Player(name="Player1", class_type="warrior")
            player2 = Player(name="Player2", class_type="mage")
            player3 = Player(name="Player3", class_type="rogue")
            player4 = Player(name="Player4", class_type="warrior")

            party = Party(Pos(14, 6), [player1, player2, player3, player4])
            party.funds = 900
            mz = gen_main_path(party.squads[0].pos, 50, 28, 13)
        mController = mazeController(mz, 28, 13, party, combat_handler)
        current_room = mz[party.squads[0].pos.y][party.squads[0].pos.x]
        if current_room:
            # current_room.enter_room(party)
            if current_room.enemies:
                combat_handler = CombatHandler(
                    party, list(party.squads[0].characters), current_room.enemies
                )


        while True:
            while combat_handler:
                result = combat_handler.combat()
                if result == CombatResult.VICTORY:
                    combat_handler = None
                    saves.save(mz, party)
                elif result == CombatResult.DEFEAT:
                    print("you lost")
                    sys.exit()
            combat_handler = mController.tick()
    finally:
        print("\033[?25h", end="")


if __name__ == "__main__":
    inputController.start()
    main()
