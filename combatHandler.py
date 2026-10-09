from maze import pretty_print
from utils import clear

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
        clear()
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
        longestName = max([len(n.name) for av, n in self.turn_order])
        additionalChars = max(0, longestName - 15)
        print("┌──────────────────────────" + "─" * additionalChars + "┐")
        print("│" + "TURN ORDER".center(26 + additionalChars) + "│")
        print("├──────────────────────────" + "─" * additionalChars + "┤")
        for av, char in self.turn_order:
            print(f"│ {char.name.ljust(15 + additionalChars)} │ {av:<3.0f} AV │")
        print("└──────────────────────────" + "─" * additionalChars + "┘")