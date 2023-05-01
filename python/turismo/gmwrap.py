"""`googlemaps` wrapper"""

from .concept import Stay

from pathlib import Path
from datetime import datetime
import random
import io
import logging

import googlemaps


class GMWrap:
    _fixed_departure_time = datetime.strptime(
        # TODO Check this means local timezone
        "2024-01-01 11:00:00",
        "%Y-%m-%d %H:%M:%S",
    )

    _map_size = (640, 480)
    _max_points_in_path_to_display = 300

    def __init__(self, *, api_key: str, direction_stash_csv_path: Path):
        self._client = googlemaps.Client(key=api_key)
        self._direction_stash_csv_path = Path(direction_stash_csv_path)

        assert self._direction_stash_csv_path.is_file()

    def get_direction_info(self, origin: str, destination: str):
        """Implemented with memoization by stash file"""
        with open(self._direction_stash_csv_path) as stash_file:
            for line in stash_file:
                if line.startswith(f"{origin},{destination}"):
                    slices = line.strip().split(",")
                    assert len(slices) == 4

                    return int(slices[2]), int(slices[3])

        result = self._client.directions(
            origin,
            destination,
            departure_time=self._fixed_departure_time,
        )

        distance_in_meter = result[0]["legs"][0]['distance']['value']
        duration_in_second = result[0]["legs"][0]['duration']['value']

        # TODO Stash full result, not just distance and duration, say directory of json
        with open(self._direction_stash_csv_path, "a") as stash_file:
            stash_file.write(f"{origin},{destination},{distance_in_meter},{duration_in_second}")
            stash_file.write("\n")

        return distance_in_meter, duration_in_second

    def _make_markers(self, stay: Stay):
        ret = []

        cur_stay = stay
        while cur_stay:
            ret.append(googlemaps.maps.StaticMapMarker(locations=[cur_stay.hotel.location.name]))
            cur_stay = cur_stay.previous

        return ret

    def _make_path(self, stay: Stay):
        points = []

        cur_stay = stay
        while cur_stay.previous:
            pre_stay = cur_stay.previous

            directions = self._client.directions(
                # TODO Use `Hotel`'s accurate coordinate
                pre_stay.hotel.location.name,
                cur_stay.hotel.location.name,
                departure_time=self._fixed_departure_time,
            )

            cur_points = googlemaps.convert.decode_polyline(
                directions[0]["overview_polyline"]["points"]
            )
            points = cur_points + points

            cur_stay = pre_stay

        # TODO use 'try again on failure' approach, on ratio based reduction
        if len(points) > self._max_points_in_path_to_display:
            final_points = [
                points[i] for i in
                sorted(random.sample(range(len(points)), self._max_points_in_path_to_display))
            ]
        else:
            final_points = points

        return googlemaps.maps.StaticMapPath(points=final_points)

    def download_itinerary_map(self, stay: Stay, output_png_path: Path):
        output_png_path = Path(output_png_path)
        assert output_png_path.suffix == ".png"

        res_iter = self._client.static_map(
            size=self._map_size,
            path=self._make_path(stay),
            markers=self._make_markers(stay),
            format="png",
        )

        html_head_magic = b"<!DOCTYPE html>"  # Hard-coded
        with io.BytesIO() as response:
            for chunk in res_iter:
                response.write(chunk)

            with response.getbuffer() as view:
                response_is_html = view[:len(html_head_magic)].tobytes() == html_head_magic

            if response_is_html:
                logging.warning("HTML generated - This may mean failure to the static map API")
                output_path = output_png_path.parent / "error.html"
            else:
                output_path = output_png_path

            with open(output_path, "wb") as map_file:
                map_file.write(response.getbuffer())
