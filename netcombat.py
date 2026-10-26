from combatHandler import CombatHandler
import time

class NetworkCombatHandler(CombatHandler):
    def __init__(self, party, players, enemies, notify, pause_seconds):
        self.notify = notify
        self.pause_seconds = pause_seconds
        super().__init__(party, players, enemies)

    def announce(self, text, typed = False):
        self.notify({"type": "log", "text": text, "typed": typed})

    def pause(self):
        time.sleep(self.pause_seconds)

    def refresh(self):
        self.notify(self.state_message())

    def state_message(self):
        return {
            "type":"combat_state",
            "turn_order":[
                {
                    "name":entry.character.name,
                    "health":entry.character.health,
                    "av": round(entry.av),
                    "is_player": entry.character in self.players
                }
                for entry in self.turn_order
            ],
        }

    def choose_action(self, player, options):
        return 0

    def choose_targets(self, options, count, minimum):
        return list(range(min(count, len(options))))
    