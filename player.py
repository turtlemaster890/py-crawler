from maze import Pos

class Player:
    def __init__(self, pos: Pos):
        self.pos = pos
        self.speed = 100
        self.max_health = 100
        self.health = self.max_health
        self.max_stamina = 100
        self.stamina = self.max_stamina

    def turnStart(self):
        self.stamina = self.max_stamina
        