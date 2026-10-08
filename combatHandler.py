

class CombatHandler:
    def __init__(self, player=None, enemy=None):
        self.player = player or []
        self.enemy = enemy or []
        self.turn_order = []
        for character in self.player + self.enemy:
            av = 10000 / character.speed
            self.turn_order.append([av, character])
        self.turn_order.sort(key=lambda x: x[0])
        for i in range(1, len(self.turn_order)):
            self.turn_order[i][0] -= self.turn_order[0][0]
        self.turn_order[0][0] = 0

    def combat(self):
        self.print_turn_order()
        print(self.turn_order[0][1].name, "is taking their turn.")
        self.turn_order[0][1].turnStart()
        self.tick_initiative()

    def tick_initiative(self):
        current_av, current_character = self.turn_order[0]

        next_av = 10000 / current_character.speed
        self.turn_order[0][0] = next_av
        self.turn_order.sort(key=lambda x: x[0])

        for i in range(1, len(self.turn_order)):
            self.turn_order[i][0] -= self.turn_order[0][0]
        self.turn_order[0][0] = 0

    def print_turn_order(self):
        print(
            "Turn order:",
            [
                f"{character.name} ({av:.2f})"
                for av, character in self.turn_order
            ]
        )