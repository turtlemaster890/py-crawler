import random

import enemy


def encounterFactory() -> list[enemy.Enemy]:
    return random.choice(
        [
            [],
            [],
            [],
            [],
            [enemy.SmallSlime(), enemy.Skeleton()],
            [
                enemy.Goblin(),
                enemy.Goblin(),
            ],
            [enemy.LargeSlime()],
            [enemy.Skeleton(), enemy.Skeleton()],
            [enemy.NormalGuy()],
            [enemy.Necromancer()],
            [enemy.Jelly() for _ in range(8)],
            [enemy.Pyromaniac()]
        ]
    )
