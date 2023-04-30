from .concept import Hotel, Stay
from .gmwrap import GMWrap

import logging


def cost_of_route(
    orig: Hotel,
    dest: Hotel,
    *,
    gmwrap: GMWrap,
    fuel_eff_in_euro_per_km: float,
    driving_cost_per_hour: float,
) -> float:
    ret = 0

    distance_in_meter, duration_in_second = gmwrap.get_direction_info(
        # TODO Use `hotel`'s accurate coordinate
        orig.location.name,
        dest.location.name,
    )

    # Fuel
    #
    # TODO Estimate more accurate value considering elevation profile
    fuel_cost = fuel_eff_in_euro_per_km * distance_in_meter / 1000
    logging.debug(f"+ {fuel_cost=}")
    ret += fuel_cost

    # Driving cost
    driving_cost = driving_cost_per_hour * duration_in_second / 3600
    logging.debug(f"+ {driving_cost=}")
    ret += driving_cost

    return ret


def cost_of_stay(stay: Stay) -> float:
    ret = 0

    location = stay.hotel.location

    hotel_cost = stay.hotel.euro_per_day * stay.days
    logging.debug(f"+ {hotel_cost=}")
    ret += hotel_cost

    joy_benefit = location.initial_joy * min(stay.days, location.recommended_days)
    logging.debug(f"- {joy_benefit=}")
    ret -= joy_benefit

    return ret
