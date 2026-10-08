from maze import Pos
from player import Player

class Party:
    def __init__(self, pos: Pos, members: list[Player]):
        self.pos = pos
        self.members = members