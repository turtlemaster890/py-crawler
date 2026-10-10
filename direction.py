from enum import Enum

class direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def opposite(self):
        return {
            direction.UP: direction.DOWN,
            direction.DOWN: direction.UP,
            direction.LEFT: direction.RIGHT,
            direction.RIGHT: direction.LEFT
        }[self]