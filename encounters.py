import random

import enemy


def encounterFactory() -> list[enemy.enemy]:
    return random.choice(
        [
            [],
            [],
            [],
            [],
            [enemy.SmallSlime(), enemy.Skeleton()],
            # [
            #     enemy.Goblin(),
            #     enemy.Goblin(),
            #     enemy.Goblin(),
            #     enemy.Goblin()
            # ],
            [enemy.LargeSlime()],
            [enemy.Skeleton(), enemy.Skeleton()],
            [enemy.NormalGuy()],
            [enemy.Necromancer()],
            [enemy.Jelly() for _ in range(8)],
        ]
    )
