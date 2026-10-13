from direction import direction


class Pos:
    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y

    def __add__(self, other) -> "Pos":
        if isinstance(other, Pos):
            return Pos(self.x + other.x, self.y + other.y)
        if isinstance(other, direction):
            return Pos(self.x + other.value[0], self.y + other.value[1])
        return NotImplemented

    def __str__(self):
        return f"P({self.x}, {self.y})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Pos):
            return self.x == other.x and self.y == other.y
        return False

    def __key(self):
        return (self.x, self.y)

    def __hash__(self):
        return hash(self.__key())

    def to_json(self):
        return self.__key()

    @classmethod
    def from_json(cls, key):
        return cls(key[0], key[1])
