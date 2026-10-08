from maze import Pos, gen_main_path, pretty_print, direction, Room
from player import Player

input_to_direction = {
    "u": direction.UP,
    "d": direction.DOWN,
    "l": direction.LEFT,
    "r": direction.RIGHT
}

def main():
    player = Player(Pos(5, 5))
    mz = gen_main_path(Pos(5, 5), 10)
    discovered = {player.pos}
    while True:
        pretty_print(mz, discovered, player.pos)
        dir = input_to_direction[input("Enter a movement direction (U, D, L, R): ").lower()]
        newPos = player.pos + dir
        currentRoom = mz[player.pos.y][player.pos.x]
        assert isinstance(currentRoom, Room)
        newRoom = mz[newPos.y][newPos.x]
        if isinstance(newRoom, Room) and currentRoom.has_connection(dir):
            discovered.add(newPos)
            player.pos = newPos

if __name__ == "__main__":
    main()