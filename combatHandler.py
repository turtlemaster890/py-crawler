class CombatHandler:
    def __init__(self, player=None, enemy=None):
        self.player = [player] if player else []
        self.enemy = [enemy] if enemy else []
        self.turn_order = []
        for ally in self.player:
            self.turn_order.append(ally.speed, ally)
        for foe in self.enemy:
            self.turn_order.append(foe.speed, foe)

    def combat_turn(self):
        self.tick_initiative()

    def tick_initiative(self):
        print("hi")
        self.turn_order[0][0] = self.turn_order[0][1].speed
        self.turn_order.sort(key=lambda x: x[0], reverse=True)
        print(f"Turn order: {[f'{x[1]} ({x[0]})' for x in self.turn_order]}")
        