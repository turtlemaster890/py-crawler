import json

from player import Player
import utils
import menuHelper

with open(utils.getRelativePath("player_stats.json")) as f:
    pStats: dict = json.load(f)
    lClasses: list[str] = list(pStats.keys())
    playerClasses: list[str] = [cl.capitalize() for cl in lClasses]


def pick_players(num_players: int) -> list[Player]:
    o: list[Player] = []
    for i in range(num_players):
        player_name: str = menuHelper.inputMenu(f"Player {i + 1}'s name", 15)
        opt: int = menuHelper.menu(player_name, playerClasses, False)
        o.append(Player(player_name, lClasses[opt]))
    return o
