from Pos import Pos
from player import Player
from party import Party
from netgame import handle_join

classes = ["warrior", "mage", "rogue", "warrior"]
party = Party(
    Pos(14, 6),
    [Player(name=f"Player{n}", class_type=c) for n, c in enumerate(classes, start=1)],
)
party.squads.clear()  # Party.__init__ makes one squad with everyone; start with none
start = Pos(14, 6)

failures = 0


def check(label, condition):
    global failures
    if not condition:
        failures += 1
    print(("PASS" if condition else "FAIL"), "-", label)


def run(label, msg, expect_ok, contains=None):
    """Send one join request and check the outcome. Returns the squad (or None)."""
    global failures
    before = len(party.squads)
    try:
        squad, err = handle_join(party, msg, start)
    except Exception as e:
        failures += 1
        print(f"FAIL - {label}: RAISED {type(e).__name__}: {e}")
        return None

    if expect_ok:
        ok = squad is not None and err is None and len(party.squads) == before + 1
        check(f"{label} (squad created, now {len(party.squads)})", ok)
    else:
        ok = squad is None and isinstance(err, str) and len(party.squads) == before
        if ok and contains is not None:
            ok = contains in err
        check(f"{label} (rejected, still {len(party.squads)} squads)", ok)
        print("       message:", err)
    return squad


# --- valid joins ---
s1 = run("join [0, 1]", {"type": "join", "characters": [0, 1]}, True)
run("join [2]", {"type": "join", "characters": [2]}, True)

# --- rejected by create_squad ---
run("already claimed [0]", {"type": "join", "characters": [0]}, False, contains="Player1")
run("empty list", {"type": "join", "characters": []}, False)
run("duplicates [3, 3]", {"type": "join", "characters": [3, 3]}, False)

# --- rejected before create_squad is reached ---
run("bad index AFTER a good one [0, 9]", {"type": "join", "characters": [0, 9]}, False)
run("out of range [9]", {"type": "join", "characters": [9]}, False)
run("negative [-1]", {"type": "join", "characters": [-1]}, False)
run("no 'characters' key", {"type": "join"}, False)
run("characters is a string", {"type": "join", "characters": "abc"}, False)
run("string inside list [0, '1']", {"type": "join", "characters": [0, "1"]}, False)
run("True inside list", {"type": "join", "characters": [True]}, False)
run("float inside list", {"type": "join", "characters": [1.0]}, False)
run("message is not a dict", "hello", False)

# --- character 3 must still be free: none of the failures above may have claimed it ---
run("join [3] after all the failures", {"type": "join", "characters": [3]}, True)

# --- the squad that came back must be the stored one, holding the real Player objects ---
print()
check("returned squad is the stored squad", s1 is party.squads[0])
check(
    "squad holds the same Player objects as party.members",
    s1 is not None
    and len(s1.characters) == 2
    and all(a is b for a, b in zip(s1.characters, party.members[:2])),
)
check("three squads in total", len(party.squads) == 3)

print()
print("ALL PASSED" if failures == 0 else f"{failures} FAILED")