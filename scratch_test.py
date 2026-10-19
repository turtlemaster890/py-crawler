from Pos import Pos
from player import Player
from party import Party

p1 = Player(name="Player1", class_type="warrior")
p2 = Player(name="Player2", class_type="mage")
p3 = Player(name="Player3", class_type="rogue")
p4 = Player(name="Player4", class_type="warrior")
stranger = Player(name="Stranger", class_type="warrior")

party = Party(Pos(14, 6), [p1, p2, p3, p4])
party.squads = []  # Party.__init__ makes one squad with everyone, so clear it


def check(label, condition):
    print(("PASS" if condition else "FAIL"), "-", label)


def expect_error(label, characters):
    before = len(party.squads)
    try:
        party.create_squad(Pos(1, 1), characters)
        print("FAIL -", label, "(no error was raised)")
    except ValueError as e:
        print("message:", e)
        check(label + " (squad count unchanged)", len(party.squads) == before)


# Test 1: first squad
s1 = party.create_squad(Pos(1, 1), [p1, p2])
check("test 1: one squad exists", len(party.squads) == 1)

# Test 2: second squad
party.create_squad(Pos(2, 2), [p3, p4])
check("test 2: two squads exist", len(party.squads) == 2)

# Test 3a: claimed character listed FIRST (p1 is already in a squad)
expect_error("test 3a: claimed first", [p1, p3])

# Test 3b: claimed character listed LAST
expect_error("test 3b: claimed last", [p3, p1])

# Test 4: character not in the party
expect_error("test 4: stranger rejected", [stranger])

# Test 5: the returned squad is the stored squad (not a second object)
check("test 5: returned squad is the stored squad", s1 is party.squads[0])

# Extra: empty list and duplicates
expect_error("extra: empty list rejected", [])
expect_error("extra: duplicates rejected", [p1, p1])