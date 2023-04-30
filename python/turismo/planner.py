from .concept import Hotel, Stay, Itinerary
from .gmwrap import GMWrap

from typing import List, Dict
import logging

from astar import AStar


class ItineraryPlanner(AStar):

    def __init__(self, *, hotels, gmwrap: GMWrap, constants: Dict):
        self._hotels = hotels
        self._gmwrap = gmwrap
        self._constants = constants

    def neighbors(self, itn: Itinerary) -> List[Itinerary]:
        ret = []

        visited_hotel_names = [stay.hotel.name for stay in itn]

        for hotel in self._hotels:
            if hotel.name in visited_hotel_names:
                continue

            _, duration_in_second = self._gmwrap.get_direction_info(
                # TODO Use `hotel`'s accurate coordinate
                itn[-1].hotel.location.name,
                hotel.location.name,
            )

            if duration_in_second > self._constants["max_driving_hour"] * 3600:
                continue

            # TODO Need to add location's other hotels stay days too
            # TODO Use better `days` range
            for days in range(1, hotel.location.recommended_days + 1):
                ret.append((*itn, Stay(hotel=hotel, days=days)))

        return ret

    def _cost_of_route(self, orig: Hotel, dest: Hotel) -> float:
        ret = 0

        distance_in_meter, duration_in_second = self._gmwrap.get_direction_info(
            # TODO Use `hotel`'s accurate coordinate
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

        joy_benefit = location.initial_joy * min(stay.days, location.recommended_days)
        logging.debug(f"- {joy_benefit=}")
        ret -= joy_benefit

        return ret

    def distance_between(self, _, itn: Itinerary) -> float:
        return self._cost_of_route(itn[-2].hotel, itn[-1].hotel) + self._cost_of_stay(itn[-1])

    def is_goal_reached(self, itn: Itinerary, _) -> bool:
        # TODO Use `self._goal`
        return itn[-1].hotel.name == self._constants["destination_hotel"]

    def heuristic_cost_estimate(self, itn: Itinerary, _) -> float:
        return 1  # TODO
