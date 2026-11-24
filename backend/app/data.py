"""
Load the pipeline's output files into memory (decision D10: no database for
the GIS data; ~6,000 road segments fit easily in RAM).
"""

import json

from .config import DATA_DIR


def _read(name, default=None):
    path = DATA_DIR / name
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"{path} missing - run scripts/fetch_chamoli_data.py first")
    return json.loads(path.read_text(encoding="utf-8"))


class AppData:
    def __init__(self):
        roads = _read("roads_segments.geojson")["features"]
        # one plain dict per segment; "coords" = [[lon, lat], ...]
        self.segments = []
        for ft in roads:
            s = dict(ft["properties"])
            s["coords"] = ft["geometry"]["coordinates"]
            self.segments.append(s)
        self.by_id = {s["segment_id"]: s for s in self.segments}

        self.boundary = _read("boundary.geojson")
        self.landslides = _read("landslides.geojson")
        self.rivers = _read("rivers.geojson")
        self.pois = _read("pois.geojson")
        self.places = _read("places.json", default=[])
        self.weather = _read("weather.json", default=[])   # replaced by the live updater
