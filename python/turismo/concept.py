from enum import Enum
from dataclasses import dataclass
from typing import Tuple

Biome = Enum("Biome", "city grass alpine desert beach")


@dataclass(frozen=True)
class Location:
    name: str
    recommended_days: int
    initial_joy: float

    # TODO
    # cost_of_living_per_day: float  # Food, coffee, ...
    # merit: float  # e.g.) merit of special activity in the location
    # biome: Biome


@dataclass(frozen=True)
class Hotel:
    name: str
    location: Location
    euro_per_day: float

    # TODO
    # include_breakfast: bool
    # extra_fee: float
    # quality: float  # View, cleaness ... / Ignored on one-night stay
    # latitude / longitude


@dataclass(frozen=True)
class Stay:
    hotel: Hotel
    days: int


# TODO Make custom list-like class with hash
Itinerary = Tuple[Stay, ...]
