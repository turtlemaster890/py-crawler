from Pos import Pos
from player import Player


class Squad:

    def __init__(self, pos: Pos, characters: list[Player]):
        self.pos = pos
        self.characters = characters
