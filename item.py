class Item:
    def __init__(self, name: str, ):
        self.name = name

class Weapon(Item):
    def __init__(self, name: str, ):
        super().__init__(name)
        self.damage = 5

class Armor(Item):
    def __init__(self, name: str, ):
        super().__init__(name)

class Relic(Item):
    def __init__(self, name: str, ):
        super().__init__(name)

class Consumable(Item):
    def __init__(self, name: str, ):
        super().__init__(name)