import game_server
import client_game

def run_local():
    import json
    import sys

    import colorama

    import inputController
    import menuHelper
    import saves
    import startMenu
    import terminalDisplay
    import utils
    from combatHandler import CombatHandler, CombatResult
    from direction import direction
    from maze import Pos, gen_main_path, maze
    from mazeController import mazeController
    from party import Party

    inputController.start()

    input_to_direction = {
        "u": direction.UP,
        "d": direction.DOWN,
        "l": direction.LEFT,
        "r": direction.RIGHT,
    }


    combat_handler: CombatHandler | None = None

    mz: maze

    party: Party


    def victory_screen(party: Party) -> bool:
        terminalDisplay.contextDisplay.type_print(
            "The stone titan crumbles to dust. A stairway opens up in the ground."
        )
        utils.wait_for_enter()
        terminalDisplay.contextDisplay.print_boxify(
            f"FLOOR {party.floor} CLEARED! Party funds: ¢{party.funds}"
        )
        utils.wait_for_enter()
        c = menuHelper.menu(
            "Floor cleared!",
            [f"Descend to floor {party.floor + 1}", "Keep Exploring", "Quit"],
            False,
        )
        if c == 2:
            utils.clear()
            raise SystemExit("Thanks for playing!")
        return c == 0


    def descend(party: Party) -> maze:
        party.descent_requested = False
        party.floor += 1
        party.squads[0].pos = Pos(14, 6)
        party.discovered_positions = {party.squads[0].pos}
        for m in party.members:
            m.health = min(m.max_health, m.health + m.max_health // 2)
            m.stamina = m.max_stamina
        return gen_main_path(party.squads[0].pos, 50, 28, 13, party.floor)


    def next_floor(party: Party):
        new_maze = descend(party)
        saves.save(new_maze, party)
        return new_maze, mazeController(new_maze, 28, 13, party)

    try:
        colorama.init(autoreset=True)
        print("\033[?25l", end="")
        w = 120
        h = 45
        sys.stdout.write(f"\x1b[8;{h};{w}t")
        utils.clear()

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
            mz = gen_main_path(party.squads[0].pos, 50, 28, 13)
        mController = mazeController(
            mz, 28, 13, party, party.squads[0].pos, CombatHandler
        )
        current_room = mz[party.squads[0].pos.y][party.squads[0].pos.x]
        if current_room and current_room.enemies:
            combat_handler = CombatHandler(
                party, list(party.squads[0].characters), current_room.enemies
            )

        while True:
            while combat_handler:
                result = combat_handler.combat()
                if result == CombatResult.VICTORY:
                    won = combat_handler.victory
                    combat_handler = None
                    saves.save(mz, party)
                    if won and victory_screen(party):
                        mz, mController = next_floor(party)
                elif result == CombatResult.DEFEAT:
                    print("you lost")
                    sys.exit()
            combat_handler = mController.tick()
            if party.descent_requested:
                mz, mController = next_floor(party)
    finally:
        print("\033[?25h", end="")


def main():
    opt = input("Standalone (1), Server Host (2) or Client (3)?\n(Standalone or client recommended, ipv6 and port forwarding required for host): ")
    match opt:
        case "1":
            print("Starting standalone...")
            run_local()
        case "2":
            game_server.host()
        case "3":
            client_game.start()
        case _:
            print(f"Invalid option: {opt}.")


if __name__ == "__main__":
    main()
