from typing import TYPE_CHECKING

from combatHandler import CombatHandler
from enemy import Enemy
from player import Player

if TYPE_CHECKING:
    from player import Player
    from enemy import Enemy
    from combatHandler import CombatHandler


class Condition:
    def __init__(
        self,
        name: str,
        duration: int,
        affected: Player | Enemy,
        handler: CombatHandler,
    ) -> None:
        self.name: str = name
        self.duration: int = duration
        self.affected: Player | Enemy = affected
        self.combat: CombatHandler = handler

    def changeDuration(self, amount: int) -> None:
        self.duration += amount
        if self.duration <= 0:
            self.affected.conditions.remove(self)

    def turnStart(self) -> None:
        self.changeDuration(-1)

    def turnEnd(self) -> None:
        pass

    def takeDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        pass

    def die(self) -> None:
        pass

    def dealDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        pass

    def enemyDeath(self, enemy: Enemy | Player) -> None:
        pass

    def inflictCondition(self, condition: Condition, target: Player | Enemy) -> None:
        pass


class Slimed(Condition):
    def __init__(
        self,
        duration: int,
        affected: Player | Enemy,
        handler: CombatHandler,
        name: str = "Slimed",
    ) -> None:
        super().__init__(name, duration, affected, handler)

    def turnStart(self) -> None:
        super().turnStart()
        self.affected.speed -= 5


class Poisoned(Condition):
    def __init__(
        self,
        duration: int,
        affected: Player | Enemy,
        handler: CombatHandler,
        name: str = "Poisoned",
    ) -> None:
        super().__init__(name, duration, affected, handler)

    def turnStart(self) -> None:
        super().turnStart()
        self.affected.takeDamage(self.combat, 2, None, "poison")


class Strength(Condition):
    def __init__(
        self,
        duration: int,
        affected: Player | Enemy,
        handler: CombatHandler,
        name: str = "Strength",
    ) -> None:
        super().__init__(name, duration, affected, handler)

    def dealDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        return amount + 2


class Weakness(Condition):
    def __init__(
        self,
        duration: int,
        affected: Player | Enemy,
        handler: CombatHandler,
        name: str = "",
    ) -> None:
        super().__init__(name, duration, affected, handler)

    def dealDamage(
        self,
        amount: int,
        attacker: Player | Enemy | None = None,
        defender: Player | Enemy | None = None,
        damage_type: str = "",
    ) -> int | None:
        return amount - 2
