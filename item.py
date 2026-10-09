class Item:
    def __init__(self, name: str, ):
        self.name = name

class Weapon(Item):
    def __init__(self, name: str, ):
        super().__init__(name)