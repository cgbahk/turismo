"""`googlemaps` wrapper"""

from pathlib import Path
from datetime import datetime

import googlemaps


class GMWrap:
    _fixed_departure_time = datetime.strptime(
        # TODO Check this means local timezone
        "2024-01-01 11:00:00",
        "%Y-%m-%d %H:%M:%S",
    )

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
