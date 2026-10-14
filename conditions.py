class condition:
    def __init__(self, name: str, duration: int, affected = None, handler = None):
        self.name = name
        self.duration = duration
        self.affected = affected
        self.combat = handler

    def changeDuration(self, amount: int):
        self.duration += amount
        if self.duration <= 0:
            self.affected.conditions.remove(self)
    
    def turnStart(self):
        pass

    def turnEnd(self):
        pass

    def takeDamage(self, amount, attacker = None, defender = None, damage_type = None):
        pass

    def die(self):
        pass

    def dealDamage(self, amount, attacker = None, defender = None, damage_type = None):
        pass

    def enemyDeath(self, enemy):
        pass

    def inflictCondition(self, condition, target):
        pass

    def equip(self, player):
        self.player = player
        pass

    def unequip(self, player):
        self.player = None
        pass