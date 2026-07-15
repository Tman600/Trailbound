"""
Core mutable state for a Trailbound run: the party, the resources,
and the journey progress. Kept free of any rendering or I/O concerns.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Character:
    name: str
    role: str
    health: int = 100          # 0-100
    alive: bool = True
    condition: str = "healthy"  # healthy / weary / critical / dead
    days_sick: int = 0

    def apply_health_delta(self, delta: int):
        if not self.alive:
            return
        self.health = max(0, min(100, self.health + delta))
        if self.health <= 0:
            self.alive = False
            self.condition = "dead"
        elif self.health < 25:
            self.condition = "critical"
        elif self.health < 60:
            self.condition = "weary"
        else:
            self.condition = "healthy"


@dataclass
class GameState:
    genre_id: str
    day: int = 1
    distance_traveled: float = 0.0
    total_distance: float = 0.0
    next_landmark_at: float = 0.0
    landmarks_passed: int = 0

    money: int = 0
    food: int = 0
    special_resource: int = 0   # ammo / fuel / scrap / mana / cannonballs
    vehicle_health: int = 100
    morale: int = 70

    pace: str = "steady"        # grueling / steady / cautious
    rations: str = "meager"     # bare / meager / filling

    party: List[Character] = field(default_factory=list)
    log: List[str] = field(default_factory=list)
    flags: Dict[str, bool] = field(default_factory=dict)

    ended: bool = False
    ending_key: Optional[str] = None
    ending_text: Optional[str] = None

    def alive_party(self) -> List[Character]:
        return [c for c in self.party if c.alive]

    def note(self, text: str):
        self.log.append(f"Day {self.day}: {text}")

    def progress_fraction(self) -> float:
        if self.total_distance <= 0:
            return 0.0
        return min(1.0, self.distance_traveled / self.total_distance)
