import json

class enemy:
    def __init__(self, name: str = "Enemy", enemy_type: str = "goblin"):
        self.enemy_type = enemy_type or "goblin"
        self.name = name or "Enemy"
        with open("enemy_stats.json", "r") as f:
            self.max_health = json.load(f)[self.enemy_type]["health"]
            self.speed = json.load(f)[self.enemy_type]["speed"]
        self.health = self.max_health

    def turnStart(self):
        input()

class Goblin(enemy):
    def __init__(self, name: str = "Goblin"):
        super().__init__(name, "goblin")
    def rob(self):
        print(f"{self.name} is robbing you!")