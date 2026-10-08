from maze import Pos, gen_main_path, pretty_print, direction, Room
from player import Player
from enemy import enemy
from combatHandler import CombatHandler

input_to_direction = {
    "u": direction.UP,
    "d": direction.DOWN,
    "l": direction.LEFT,
    "r": direction.RIGHT
}

def main():

    player1 = Player(Pos(5, 5), name="Player1", speed=250)
    player2 = Player(Pos(5, 5), name="Player2", speed=94)
    player3 = Player(Pos(5, 5), name="Player3", speed=85)
    player4 = Player(Pos(5, 5), name="Player4", speed=140)
    enemy1 = enemy(name="Enemy1", speed=78)
    enemy2 = enemy(name="Enemy2", speed=90)
    combat_handler = CombatHandler([player1, player2, player3, player4], [enemy1, enemy2])
    while True:
        combat_handler.combat_turn()

    # player = Player(Pos(5, 5))
    # mz = gen_main_path(Pos(5, 5), 10)
    # discovered = {player.pos}
    
    # while True:
    #     pretty_print(mz, discovered, player.pos)
    #     dir = input_to_direction[input("Enter a movement direction (U, D, L, R): ").lower()]
    #     newPos = player.pos + dir
    #     currentRoom = mz[player.pos.y][player.pos.x]
    #     assert isinstance(currentRoom, Room)
    #     newRoom = mz[newPos.y][newPos.x]
    #     if isinstance(newRoom, Room) and currentRoom.has_connection(dir):
    #         discovered.add(newPos)
    #         player.pos = newPos

    

if __name__ == "__main__":
    main()