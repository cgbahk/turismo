from .concept import Hotel, Stay
from .gmwrap import GMWrap

from typing import Iterable, Dict, Set
import logging
from dataclasses import dataclass

from astar import AStar


class ItineraryPlanner(AStar):
    """NOTE Need to pass goal condition by ctor, not `astar()`"""

    @dataclass
    class Goal:
        final_stay_hotel: Hotel
        total_days: int
        max_try: int

    # TODO Can `initial` be removed?
    def __init__(self, *, hotels, goal: Goal, gmwrap: GMWrap, constants: Dict, initial: Stay):
        self._hotels = hotels
        self._gmwrap = gmwrap
        self._constants = constants
        self._cost_of = {initial: 0}

        # Goal related
        self._goal = goal
        self._cur_try_count = 0
        self._cur_min_cost = float("inf")

    def _get_visited_hotel_names(self, stay: Stay) -> Set[str]:
        ret = set()
        cur_stay = stay

        while cur_stay:
            ret.add(cur_stay.hotel.name)
            cur_stay = cur_stay.previous

        return ret

    def neighbors(self, stay: Stay) -> Iterable[Stay]:
        visited_hotel_names = self._get_visited_hotel_names(stay)
        elapsed_days = self._get_elapsed_days(stay)

        for cand_hotel in self._hotels:
            if cand_hotel.name in visited_hotel_names:
                continue

            _, duration_in_second = self._gmwrap.get_direction_info(
                # TODO Use `Hotel`'s accurate coordinate
                stay.hotel.location.name,
                cand_hotel.location.name,
            )

            if duration_in_second > self._constants["max_driving_hour"] * 3600:
                continue

            # TODO Need to add location's other hotels stay days too
            # TODO Use better `days` range
            for days in range(1, cand_hotel.location.recommended_days + 3):
                if elapsed_days + days > self._goal.total_days:
                    continue

                yield Stay(
                    previous=stay,
                    hotel=cand_hotel,
                    days=days,
                )

    def _cost_of_route(self, orig: Hotel, dest: Hotel) -> float:
        ret = 0

        distance_in_meter, duration_in_second = self._gmwrap.get_direction_info(
            # TODO Use `Hotel`'s accurate coordinate
            orig.location.name,
            dest.location.name,
        )

        # Fuel
        #
        # TODO Estimate more accurate value considering elevation profile
        fuel_cost = self._constants["fuel_eff_in_euro_per_km"] * distance_in_meter / 1000
        logging.debug(f"+ {fuel_cost=}")
        ret += fuel_cost

        # Driving cost
        driving_cost = self._constants["driving_cost_per_hour"] * duration_in_second / 3600
        logging.debug(f"+ {driving_cost=}")
        ret += driving_cost

        return ret

    def _cost_of_stay(self, stay: Stay) -> float:
        ret = 0

        location = stay.hotel.location

        hotel_cost = stay.hotel.euro_per_day * stay.days
        logging.debug(f"+ {hotel_cost=}")
        ret += hotel_cost

        if stay.days > location.recommended_days:
            joy_benefit = 0
        else:
            joy_half_life_in_day = 1  # TODO Take value from input
            joy_benefit = \
                location.initial_joy * \
                0.5 ** ((stay.days - 1) / joy_half_life_in_day)
            logging.debug(f"- {joy_benefit=}")
        ret -= joy_benefit

        return ret

    def distance_between(self, orig: Stay, dest: Stay) -> float:
        assert orig is dest.previous
        assert orig in self._cost_of
        assert dest not in self._cost_of

        ret = self._cost_of_route(orig.hotel, dest.hotel) + self._cost_of_stay(dest)
        self._cost_of[dest] = self._cost_of[orig] + ret

        return ret

    def _get_elapsed_days(self, stay: Stay) -> int:
        ret = 0
        cur_stay = stay

        while cur_stay:
            ret += cur_stay.days
            cur_stay = cur_stay.previous

        return ret

    def is_goal_reached(self, stay: Stay, _) -> bool:
        if stay.hotel.name != self._goal.final_stay_hotel.name:
            return False

        if self._get_elapsed_days(stay) != self._goal.total_days:
            return False

        # At this point, "some" goal reached, but may try more for better result
        #
        # TODO Ready for search space exhaust, which is possible when best solution found early.

        if self._cost_of[stay] >= self._cur_min_cost:
            return False

        self._cur_min_cost = self._cost_of[stay]

        self._cur_try_count += 1

        logging.debug(f"Try #{self._cur_try_count} / cost {self._cost_of[stay]}")
        cur_stay = stay
        while cur_stay:
            logging.debug(f"{cur_stay.hotel.name}\t{cur_stay.days}")
            cur_stay = cur_stay.previous
        logging.debug("\n")

        if self._cur_try_count < self._goal.max_try:
            return False

        return True

    def heuristic_cost_estimate(self, stay: Stay, _) -> float:
        return 1  # TODO
