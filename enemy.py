import json

class enemy:
    def __init__(self, name: str = "Enemy", enemy_type: str = "goblin"):
        self.enemy_type = enemy_type or "goblin"
        self.name = name or "Enemy"
        with open("enemy_stats.json", "r") as f:
            self.stats = json.load(f)[self.enemy_type]
            self.max_health = self.stats["health"]
            self.speed = self.stats["speed"]
        self.health = self.max_health

    def turnStart(self):
        input()

class Goblin(enemy):
    def __init__(self, name: str = "Goblin"):
        super().__init__(name, "goblin")
    def rob(self):
        print(f"{self.name} is robbing you!")