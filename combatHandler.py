from maze import pretty_print
# from utils import clear
import utils
import terminalDisplay
from typing import TYPE_CHECKING
from dataclasses import dataclass
from turnEntry import TurnEntry
if TYPE_CHECKING:
    from player import Player
    from enemy import enemy
    from party import Party

class CombatHandler:
    def __init__(self, party: Party, players: list[Player] | None = None, enemies: list[enemy] | None = None):
        self.party = party
        self.players = players or []
        self.enemies = enemies or []
        self.turn_order: list[TurnEntry] = []
        for character in self.players + self.enemies:
            av: float = 10000 / character.speed
            self.turn_order.append(TurnEntry(av, character))
        self.turn_order.sort(key=lambda x: x.av)
        for i in range(1, len(self.turn_order)):
            self.turn_order[i].av -= self.turn_order[0].av
        self.turn_order[0].av = 0
        # utils.addPrintFunction("combat", self.print_turn_order, 10)
        terminalDisplay.combatDisplay.messageProvider = self.print_turn_order_list

    def addEnemy(self, enemy: enemy):
        self.turn_order.append(TurnEntry(10000 / enemy.speed, enemy))

    def removeEnemy(self, enemy: enemy):
        for i, entry in enumerate(self.turn_order):
            if entry.character is enemy:
                del self.turn_order[i]
                return

    def combat(self):
        # clear()
        # self.print_turn_order()
        # utils.printSequences()
        terminalDisplay.updateDisplays()
        print(self.turn_order[0].character.name, "is taking their turn.")
        self.turn_order[0].character.turnStart(self)
        self.tick_initiative()

    def tick_initiative(self):
        current_av, current_character = self.turn_order[0].av, self.turn_order[0].character

        next_av = 10000 / current_character.speed
        self.turn_order[0].av = next_av
        self.turn_order.sort(key=lambda x: x.av)

        for i in range(1, len(self.turn_order)):
            self.turn_order[i].av -= self.turn_order[0].av
        self.turn_order[0].av = 0

    def print_turn_order(self):
        longestName = max(len(entry.character.name) for entry in self.turn_order)
        additionalChars = max(0, longestName - 15)
        print("┌──────────────────────────" + "─" * additionalChars + "┐")
        print("│" + "TURN ORDER".center(26 + additionalChars) + "│")
        print("├──────────────────────────" + "─" * additionalChars + "┤")
        for entry in self.turn_order:
            print(f"│ {entry.character.name.ljust(15 + additionalChars)} │ {entry.av:<3.0f} AV │")
        print("└──────────────────────────" + "─" * additionalChars + "┘")

    def print_turn_order_list(self, w: int, h: int) -> list[str]:
        out = []
        # "│ " (2) + " │ " (3) + " ### AV │" (8) = 13 characters
        nameSpace = w - 13
        
        # longestName = max(len(entry.character.name) for entry in self.turn_order)
        # additionalChars = max(0, longestName - 15)


        out.append("┌" + "─" * (w - 2) + "┐")
        out.append("│" + "TURN ORDER".center(w - 2) + "│")
        out.append("├" + "─" * (w - 2) + "┤")
        for entry in self.turn_order:
            name = entry.character.name[:nameSpace].ljust(nameSpace)
            av_str = f"{entry.av:<3.0f}"
            out.append(f"│ {name} │ {av_str} AV │")
        out.append("└" + "─" * (w - 2) + "┘")
        return out