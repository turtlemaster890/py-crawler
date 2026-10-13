from maze import Pos, gen_main_path, pretty_print, maze
from direction import direction
from player import Player
from party import Party
from pathlib import Path
import enemy
import json
from combatHandler import CombatHandler
from mazeController import mazeController
from item import Item, Weapon
from shop import Shop
import saves
import terminalDisplay
import utils
import colorama

input_to_direction = {
    "u": direction.UP,
    "d": direction.DOWN,
    "l": direction.LEFT,
    "r": direction.RIGHT,
}

SAVE_LOCATION = Path("saves/")
save_index = 0
save_file = utils.getRelativePath(SAVE_LOCATION.joinpath(f"save_{save_index}.json"))

combat_handler: CombatHandler | None = None

mz: maze

party: Party


def main():
    global party, mz, combat_handler
    try:
        colorama.init(autoreset=True)
        utils.clear()
        print("\033[?25l", end="")

        try:
            with open(save_file, "r") as f:
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
            mz = gen_main_path(party.pos, 50, 28, 13)

        mController = mazeController(mz, 28, 13, party)
        current_room = mz[party.pos.y][party.pos.x]
        if current_room:
            current_room.enter_room(party)
            if current_room.enemies:
                combat_handler = CombatHandler(
                    party, party.members, current_room.enemies
                )

        while True:
            while combat_handler:
                if not combat_handler.combat():
                    combat_handler = None
            combat_handler = mController.tick()
    finally:
        SAVE_LOCATION.mkdir(parents=True, exist_ok=True)
        with open(save_file, "w") as f:
            json.dump(saves.save(mz, party), f, indent=4)
        print("\033[?25h", end="")


if __name__ == "__main__":
    main()
