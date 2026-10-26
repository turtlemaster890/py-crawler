import random
from typing import Callable

import enemy

# min floor, weight, factory

ENCOUNTERS: list[tuple[int, int, Callable[[], list[enemy.Enemy]]]] = [
    (1, 3, lambda: [enemy.SmallSlime(), enemy.Skeleton()]),
    (1, 3, lambda: [enemy.Goblin(), enemy.Goblin()]),
    (1, 2, lambda: [enemy.LargeSlime()]),
    (1, 2, lambda: [enemy.Skeleton(), enemy.Skeleton()]),
    (2, 2, lambda: [enemy.Necromancer()]),
    (2, 2, lambda: [enemy.Pyromaniac()]),
    (2, 1, lambda: [enemy.Jelly() for _ in range(8)]),
    (3, 2, lambda: [enemy.Wolf(), enemy.Wolf()]),
    (3, 2, lambda: [enemy.NormalGuy()]),
    (3, 2, lambda: [enemy.LargeSlime(), enemy.LargeSlime()]),
    (3, 2, lambda: [enemy.Goblin(), enemy.Goblin(), enemy.Pyromaniac()]),
    (4, 2, lambda: [enemy.Necromancer(), enemy.Skeleton(), enemy.Skeleton()]),
    (4, 2, lambda: [enemy.Werewolf(), enemy.Wolf()]),
    (4, 2, lambda: [enemy.Pyromaniac(), enemy.Necromancer()]),
]


def encounterFactory(floor: int = 1) -> list[enemy.Enemy]:
    options = [(w, f) for min_floor, w, f in ENCOUNTERS if floor >= min_floor]
    options.append((max(1, 10 - floor), lambda: []))
    return random.choices(options, [o[0] for o in options])[0][1]()
