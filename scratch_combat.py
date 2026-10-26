from Pos import Pos
from player import Player
from party import Party
from enemy import Goblin, Skeleton
from combatHandler import CombatResult
from netcombat import NetworkCombatHandler

players = [
    Player(name="Player1", class_type="warrior"),
    Player(name="Player2", class_type="mage"),
]
party = Party(Pos(14, 6), players)
enemies = [Goblin(), Skeleton()]

messages = []
handler = NetworkCombatHandler(party, list(players), enemies, notify=messages.append)

turns = 0
result = CombatResult.CONTINUE
while result is CombatResult.CONTINUE and turns < 500:
    result = handler.combat()
    turns += 1

logs = [m["text"] for m in messages if m["type"] == "log"]
states = [m for m in messages if m["type"] == "combat_state"]

print("result:", result.name, "after", turns, "calls to combat()")
print("log lines:", len(logs), "| state messages:", len(states))
print()
print("--- first 8 log lines ---")
for line in logs[:8]:
    print(" ", line)
print()
print("--- first state message ---")
print(states[0])
print("--- last state message ---")
print(states[-1])
print()
print("players left:", [(p.name, p.health) for p in handler.players])
print("enemies left:", [(e.name, e.health) for e in handler.enemies])