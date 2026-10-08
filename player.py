from maze import Pos

class Player:
    def __init__(self, pos: Pos, name: str = "Player", speed: int = 100):
        self.pos = pos
        self.speed = speed
        self.max_health = 100
        self.health = self.max_health
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.name = name

    def turnStart(self):
        self.stamina = self.max_stamina
        