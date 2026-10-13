import random

import enemy


encounters = [
    [
        
    ],
    [
        enemy.SmallSlime(),
        enemy.Skeleton()
    ],
    [
        enemy.Goblin(),
        enemy.Goblin(),
        enemy.Goblin(),
        enemy.Goblin()
    ],
    [
        enemy.LargeSlime()
    ],
    [
        enemy.Skeleton(),
        enemy.Skeleton()
    ]
]

def encounterFactory() -> list[enemy.enemy]:
    return random.choice(encounters)