#!/usr/bin/env python3
"""
SafeYatra - Step 1: fetch and pre-process the GIS data for Chamoli district.

What it does (see project_context.md, section 13):
    1. District boundary        (Nominatim, Overpass fallback)
    2. Road network             (Overpass)
    3. Points of interest       (Overpass: hospitals, police, fuel ...)
    3b. Rivers and streams      (Overpass)
    4. Landslides               (NASA COOLR / Global Landslide Catalog + manual GSI file)
    5. Manual datasets          (GSI susceptibility, accidents.csv)
    6. Weather                  (Open-Meteo, 10 key towns)
    7. Road segmentation        (split ways into <= N metre pieces)
    8. Elevation                (AWS Terrain Tiles, or Open-Meteo elevation API)
    9. Geometry attributes      (curvature, sharp turns)
   10. Proximity attributes     (landslides / accidents / hospitals near each segment)
   10b. River attributes        (distance to river, stream crossings)
   11. Preview risk score       (weights from section 10.4)
   12. Optional extras          (TomTom incidents, OpenTopography DEM)
   13. Output                   (summary JSON on stdout + files in output/)

Only `requests` + the Python standard library are used, so the script is easy
to run anywhere. The GeoPandas/QGIS version of the analysis comes in phase 2.

Usage:
    python scripts/fetch_chamoli_data.py
    python scripts/fetch_chamoli_data.py --only boundary,roads --refresh
"""

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "cache"
MANUAL_DIR = ROOT / "data" / "manual"

DISTRICT_QUERY = "Chamoli district, Uttarakhand, India"
EXPECTED_AREA_KM2 = 7700            # approximate, used only for the sanity check
EXPECTED_BBOX = (78.9, 29.9, 80.1, 31.1)  # lon_min, lat_min, lon_max, lat_max

NOMINATIM_URL = "https://nominatim.openstreetmap.org"
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ELEVATION = "https://api.open-meteo.com/v1/elevation"

# NASA COOLR ArcGIS services. These moved/died in 2025-26, so they are tried
# first and the Global Landslide Catalog CSV export is used as the fallback.
NASA_COOLR_LAYERS = [
    "https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Reports_Points/FeatureServer/0",
    "https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Reports_Points/MapServer/0",
]
NASA_GLC_CSV = ("https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/"
                "Global_Landslide_Catalog_Export_rows.csv")

# Key towns (approximate coordinates from the project brief) - used for weather
# sampling and for the sanity checks.
TOWNS = [
    ("Gopeshwar", 30.408, 79.320),
    ("Chamoli", 30.402, 79.333),
    ("Joshimath", 30.555, 79.565),
    ("Badrinath", 30.743, 79.494),
    ("Govindghat", 30.620, 79.560),
    ("Pipalkoti", 30.429, 79.427),
    ("Nandprayag", 30.333, 79.317),
    ("Karnaprayag", 30.263, 79.217),
    ("Tharali", 30.075, 79.493),
    ("Gairsain", 30.050, 79.287),
]

MAIN_CLASSES = ["motorway", "trunk", "primary", "secondary", "tertiary"]
ALL_CLASSES = MAIN_CLASSES + ["unclassified", "residential"]
# Lower number = more important road (used to prioritise elevation sampling)
CLASS_RANK = {c: i for i, c in enumerate(ALL_CLASSES)}

# Static risk weights (project_context.md section 10.4)
RISK_WEIGHTS = {
    "susceptibility": 0.30,
    "landslide_density": 0.20,
    "terrain_slope": 0.20,
    "curvature": 0.15,
    "accident_density": 0.15,
}
SUSC_SCORE = {1: 0.1, 2: 0.4, 3: 0.7, 4: 1.0}
# NASA's global map is ~1 km and rates almost all of Chamoli "very high", so it
# gets a lower weight than detailed GSI data (0.30 would turn most roads "high")
NASA_SUSC_WEIGHT = 0.10
SEVERITY_WEIGHT = {"fatal": 3, "grievous": 2, "minor": 1}
# NASA records with a location accuracy worse than this are usually placed on
# the town / district centre, so they are kept in landslides.geojson but not
# used for the per-segment risk attributes.
PRECISE_LOCATIONS = {"exact", "1km", "5km", "10km", "gsi_inventory",
                     # values used in data/manual/web_landslides.csv
                     "stream-crossing", "village-level", "approximate"}

EARTH_RADIUS_M = 6371008.8
IST = timezone(timedelta(hours=5, minutes=30))

WARNINGS = []   # collected and printed in the summary


def log(msg):
    """Progress messages go to stderr so stdout stays clean JSON."""
    print(f"[{datetime.now():%H:%M:%S}] {msg}", file=sys.stderr, flush=True)


def warn(msg):
    WARNINGS.append(msg)
    log("WARNING: " + msg)


def load_dotenv(path):
    """Tiny .env reader (KEY=VALUE per line) so we don't need python-dotenv."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# --------------------------------------------------------------------------- #
# HTTP helper with cache + retries
# --------------------------------------------------------------------------- #

class Http:
    def __init__(self, refresh=False):
        self.refresh = refresh
        self.session = requests.Session()
        contact = os.environ.get("CONTACT_EMAIL", "").strip()
        ua = "SafeYatra/0.1 (student project"
        ua += f"; contact: {contact})" if contact else ")"
        self.session.headers["User-Agent"] = ua
        self.last_nominatim_call = 0.0
        CACHE_DIR.mkdir(exist_ok=True)

    def _cache_path(self, method, url, params, data, ext):
        key = json.dumps([method, url, params, data], sort_keys=True)
        return CACHE_DIR / (hashlib.sha1(key.encode()).hexdigest() + ext)

    def fetch(self, url, params=None, data=None, method="GET", timeout=60,
              retries=3, as_json=True, binary=False):
        """Return parsed JSON (or text/bytes). Responses are cached on disk."""
        ext = ".bin" if binary else (".json" if as_json else ".txt")
        cache_file = self._cache_path(method, url, params, data, ext)
        if cache_file.exists() and not self.refresh:
            if binary:
                return cache_file.read_bytes()
            text = cache_file.read_text(encoding="utf-8")
            return json.loads(text) if as_json else text

        # Nominatim usage policy: max 1 request per second
        if "nominatim" in url:
            wait = 1.1 - (time.time() - self.last_nominatim_call)
            if wait > 0:
                time.sleep(wait)
            self.last_nominatim_call = time.time()

        last_error = None
        for attempt in range(retries):
            try:
                resp = self.session.request(method, url, params=params, data=data,
                                            timeout=timeout)
                if resp.status_code in (429, 502, 503, 504):
                    raise requests.HTTPError(f"HTTP {resp.status_code}")
                resp.raise_for_status()
                if binary:
                    cache_file.write_bytes(resp.content)
                    return resp.content
                body = resp.json() if as_json else resp.text   # validates JSON
                cache_file.write_text(resp.text, encoding="utf-8")
                return body
            except (requests.RequestException, ValueError) as err:
                last_error = err
                if attempt < retries - 1:
                    delay = 2 ** (attempt + 1)
                    log(f"  request failed ({err}); retrying in {delay}s")
                    time.sleep(delay)
        raise RuntimeError(f"{url} failed after {retries} tries: {last_error}")

    def overpass(self, query, timeout=300):
        """Run an Overpass query, trying each mirror in turn."""
        for mirror in OVERPASS_MIRRORS:
            try:
                log(f"  Overpass: {mirror}")
                return self.fetch(mirror, data={"data": query}, method="POST",
                                  timeout=timeout, retries=2)
            except RuntimeError as err:
                log(f"  mirror failed: {err}")
        raise RuntimeError("all Overpass mirrors failed")


# --------------------------------------------------------------------------- #
# Geometry helpers (pure Python, lon/lat in degrees)
# --------------------------------------------------------------------------- #

def haversine(p1, p2):
    """Distance in metres between two (lon, lat) points."""
    lon1, lat1 = map(math.radians, p1)
    lon2, lat2 = map(math.radians, p2)
    a = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bearing(p1, p2):
    """Compass bearing in degrees from p1 to p2."""
    lon1, lat1 = map(math.radians, p1)
    lon2, lat2 = map(math.radians, p2)
    x = math.sin(lon2 - lon1) * math.cos(lat2)
    y = (math.cos(lat1) * math.sin(lat2)
         - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1))
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def offset_point(p, bearing_deg, dist_m):
    """Move a (lon, lat) point dist_m metres in a given direction (flat-earth, fine for < 1 km)."""
    lon, lat = p
    b = math.radians(bearing_deg)
    dlat = dist_m * math.cos(b) / EARTH_RADIUS_M
    dlon = dist_m * math.sin(b) / (EARTH_RADIUS_M * math.cos(math.radians(lat)))
    return (lon + math.degrees(dlon), lat + math.degrees(dlat))


class LocalProjection:
    """Equirectangular projection to metres around a reference latitude.
    Accurate to well under 1 % inside one district - good enough for v1."""

    def __init__(self, lat0):
        self.kx = math.radians(1) * EARTH_RADIUS_M * math.cos(math.radians(lat0))
        self.ky = math.radians(1) * EARTH_RADIUS_M

    def __call__(self, p):
        return (p[0] * self.kx, p[1] * self.ky)


def point_segment_dist(p, a, b):
    """Distance from point p to line piece a-b (all in projected metres)."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def point_line_dist(p, line_xy):
    return min(point_segment_dist(p, line_xy[i], line_xy[i + 1])
               for i in range(len(line_xy) - 1))


def point_in_ring(pt, ring):
    """Ray casting test. ring = list of [lon, lat]."""
    x, y = pt
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def point_in_geometry(pt, geom):
    """Point-in-polygon for GeoJSON Polygon / MultiPolygon (holes respected)."""
    if geom["type"] == "Polygon":
        polygons = [geom["coordinates"]]
    elif geom["type"] == "MultiPolygon":
        polygons = geom["coordinates"]
    else:
        return False
    for rings in polygons:
        if point_in_ring(pt, rings[0]) and not any(point_in_ring(pt, h) for h in rings[1:]):
            return True
    return False


def geometry_area_km2(geom):
    """Polygon area with the shoelace formula on a local projection."""
    polygons = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    lat0 = polygons[0][0][0][1]
    proj = LocalProjection(lat0)

    def ring_area(ring):
        xy = [proj(p) for p in ring]
        return abs(sum(xy[i][0] * xy[i + 1][1] - xy[i + 1][0] * xy[i][1]
                       for i in range(len(xy) - 1))) / 2

    total = 0.0
    for rings in polygons:
        total += ring_area(rings[0]) - sum(ring_area(h) for h in rings[1:])
    return total / 1e6


def geometry_bbox(geom):
    polygons = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    lons = [p[0] for rings in polygons for p in rings[0]]
    lats = [p[1] for rings in polygons for p in rings[0]]
    return [min(lons), min(lats), max(lons), max(lats)]


def centroid(geom):
    """Rough centroid (vertex average) - enough for turning landslide polygons into points."""
    t = geom["type"]
    if t == "Point":
        return tuple(geom["coordinates"][:2])
    if t == "Polygon":
        pts = geom["coordinates"][0]
    elif t == "MultiPolygon":
        pts = [p for poly in geom["coordinates"] for p in poly[0]]
    elif t == "LineString":
        pts = geom["coordinates"]
    elif t == "MultiPoint":
        pts = geom["coordinates"]
    else:
        return None
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def line_length(coords):
    return sum(haversine(coords[i], coords[i + 1]) for i in range(len(coords) - 1))


def point_along(coords, fraction):
    """Point at a fraction (0..1) of the way along a line, plus the local bearing."""
    target = line_length(coords) * fraction
    run = 0.0
    for i in range(len(coords) - 1):
        d = haversine(coords[i], coords[i + 1])
        if run + d >= target and d > 0:
            t = (target - run) / d
            p = (coords[i][0] + t * (coords[i + 1][0] - coords[i][0]),
                 coords[i][1] + t * (coords[i + 1][1] - coords[i][1]))
            return p, bearing(coords[i], coords[i + 1])
        run += d
    return tuple(coords[-1]), bearing(coords[-2], coords[-1])


def feature(geom_type, coords, props):
    return {"type": "Feature", "geometry": {"type": geom_type, "coordinates": coords},
            "properties": props}


def feature_collection(features):
    return {"type": "FeatureCollection", "features": features}


# --------------------------------------------------------------------------- #
# 1. Boundary
# --------------------------------------------------------------------------- #

def fetch_boundary(http):
    log("1. Boundary: searching Nominatim")
    results = http.fetch(f"{NOMINATIM_URL}/search",
                         params={"q": DISTRICT_QUERY, "format": "jsonv2",
                                 "polygon_geojson": 1, "limit": 5})
    best = None
    for r in results:
        if r.get("osm_type") == "relation" and r.get("category", r.get("class")) == "boundary":
            best = r
            break

    if best is None:
        # Fallback: find the relation id with Overpass, then ask Nominatim for its polygon
        warn("Nominatim search gave no boundary relation; trying Overpass")
        q = """[out:json][timeout:180];
area["name"="Uttarakhand"]["admin_level"="4"]->.st;
rel(area.st)["boundary"="administrative"]["admin_level"="5"]["name"~"Chamoli"];
out ids tags;"""
        rels = http.overpass(q)["elements"]
        if not rels:
            raise RuntimeError("could not find the Chamoli boundary relation")
        lookup = http.fetch(f"{NOMINATIM_URL}/lookup",
                            params={"osm_ids": f"R{rels[0]['id']}", "format": "jsonv2",
                                    "polygon_geojson": 1})
        best = lookup[0]

    rel_id = int(best["osm_id"])
    geom = best["geojson"]
    boundary = {
        "name": "Chamoli",
        "display_name": best.get("display_name"),
        "osm_relation_id": rel_id,
        "overpass_area_id": 3600000000 + rel_id,
        "geometry": geom,
        "bbox": [round(v, 4) for v in geometry_bbox(geom)],
        "area_km2": round(geometry_area_km2(geom), 1),
    }
    log(f"   relation {rel_id}, area {boundary['area_km2']} km2, bbox {boundary['bbox']}")
    return boundary


# --------------------------------------------------------------------------- #
# 2. Roads
# --------------------------------------------------------------------------- #

def fetch_roads(http, boundary, road_classes):
    classes = MAIN_CLASSES if road_classes == "main" else ALL_CLASSES
    log(f"2. Roads: Overpass ({road_classes}: {', '.join(classes)})")
    pattern = "^(" + "|".join(classes) + ")(_link)?$"
    query = f"""[out:json][timeout:300];
area(id:{boundary['overpass_area_id']})->.a;
way(area.a)["highway"~"{pattern}"];
out body geom;"""
    data = http.overpass(query, timeout=360)

    ways = []
    for el in data["elements"]:
        if el.get("type") != "way" or not el.get("geometry"):
            continue
        if any(g is None for g in el["geometry"]):
            continue
        tags = el.get("tags", {})
        ways.append({
            "osm_id": el["id"],
            "highway": tags.get("highway"),
            "name": tags.get("name"),
            "ref": tags.get("ref"),
            "surface": tags.get("surface"),
            "lanes": tags.get("lanes"),
            "width": tags.get("width"),
            "maxspeed": tags.get("maxspeed"),
            "oneway": tags.get("oneway"),
            "bridge": tags.get("bridge"),
            "tunnel": tags.get("tunnel"),
            "nodes": el["nodes"],
            "coords": [(g["lon"], g["lat"]) for g in el["geometry"]],
        })
    log(f"   {len(ways)} ways")
    return ways


# --------------------------------------------------------------------------- #
# 3. Points of interest
# --------------------------------------------------------------------------- #

def poi_category(tags):
    amenity = tags.get("amenity")
    if amenity in ("hospital", "clinic", "doctors", "police", "fuel"):
        return amenity
    if tags.get("emergency") == "ambulance_station":
        return "ambulance"
    hc = tags.get("healthcare")
    if hc in ("hospital", "clinic", "doctor"):
        return "clinic" if hc != "hospital" else "hospital"
    if hc in ("centre", "health_centre"):
        return "clinic"
    return "healthcare_other" if hc else "other"


def fetch_pois(http, boundary):
    log("3. POIs: hospitals, clinics, police, fuel, ambulance")
    query = f"""[out:json][timeout:180];
area(id:{boundary['overpass_area_id']})->.a;
( nwr(area.a)["amenity"~"^(hospital|clinic|doctors|police|fuel)$"];
  nwr(area.a)["healthcare"];
  nwr(area.a)["emergency"="ambulance_station"]; );
out center tags;"""
    data = http.overpass(query)
    pois, seen = [], set()
    for el in data["elements"]:
        key = (el["type"], el["id"])
        if key in seen:
            continue
        seen.add(key)
        if el["type"] == "node":
            lon, lat = el["lon"], el["lat"]
        elif "center" in el:
            lon, lat = el["center"]["lon"], el["center"]["lat"]
        else:
            continue
        tags = el.get("tags", {})
        pois.append({"id": f"{el['type'][0]}{el['id']}", "osm_id": el["id"],
                     "category": poi_category(tags), "name": tags.get("name"),
                     "phone": tags.get("phone") or tags.get("contact:phone"),
                     "lon": lon, "lat": lat})
    log(f"   {len(pois)} POIs: {dict(Counter(p['category'] for p in pois))}")
    return pois


PLACE_RANK = {"town": 0, "village": 1, "hamlet": 2, "locality": 3}


def fetch_places(http, boundary):
    """Town / village / hamlet names for the app's place search box."""
    log("3c. Places: towns and villages for search")
    query = f"""[out:json][timeout:180];
area(id:{boundary['overpass_area_id']})->.a;
node(area.a)["place"~"^(town|village|hamlet|locality)$"]["name"];
out body;"""
    data = http.overpass(query)
    places = [{"name": t[0], "kind": "town", "lat": t[1], "lon": t[2]} for t in TOWNS]
    seen = {p["name"].lower() for p in places}
    for el in data["elements"]:
        tags = el.get("tags", {})
        name = tags.get("name:en") or tags["name"]
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        places.append({"name": name, "kind": tags["place"], "lat": el["lat"], "lon": el["lon"]})
    places.sort(key=lambda p: (PLACE_RANK.get(p["kind"], 9), p["name"]))
    log(f"   {len(places)} places: {dict(Counter(p['kind'] for p in places))}")
    return places


# --------------------------------------------------------------------------- #
# 3b. Rivers and streams
# --------------------------------------------------------------------------- #

def fetch_rivers(http, boundary):
    """Rivers (Alaknanda, Pindar, ...) and streams / nalas from OSM."""
    log("3b. Rivers and streams: Overpass")
    query = f"""[out:json][timeout:180];
area(id:{boundary['overpass_area_id']})->.a;
way(area.a)["waterway"~"^(river|stream)$"];
out tags geom;"""
    data = http.overpass(query)
    rivers = []
    for el in data["elements"]:
        geom = el.get("geometry")
        if el.get("type") != "way" or not geom or any(g is None for g in geom):
            continue
        tags = el.get("tags", {})
        coords = [(g["lon"], g["lat"]) for g in geom]
        rivers.append({"osm_id": el["id"], "kind": tags["waterway"], "name": tags.get("name"),
                       "length_m": round(line_length(coords), 1), "coords": coords})
    kinds = Counter(r["kind"] for r in rivers)
    log(f"   {kinds.get('river', 0)} river ways, {kinds.get('stream', 0)} stream ways")
    return rivers


# --------------------------------------------------------------------------- #
# 4. Landslides (NASA) + 5. manual datasets
# --------------------------------------------------------------------------- #

def fetch_nasa_coolr(http, bbox):
    """Query a COOLR ArcGIS layer with the bbox (paginated). Returns None if unavailable."""
    for layer in NASA_COOLR_LAYERS:
        records, offset = [], 0
        try:
            while True:
                page = http.fetch(f"{layer}/query", timeout=60, retries=1, params={
                    "where": "1=1", "geometry": ",".join(map(str, bbox)),
                    "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                    "spatialRel": "esriSpatialRelIntersects", "outFields": "*",
                    "outSR": 4326, "f": "json", "resultOffset": offset,
                    "resultRecordCount": 1000})
                if "error" in page:
                    raise RuntimeError(page["error"])
                for f in page.get("features", []):
                    g = f.get("geometry") or {}
                    if "x" in g:
                        records.append({**f["attributes"], "longitude": g["x"],
                                        "latitude": g["y"]})
                if not page.get("exceededTransferLimit"):
                    break
                offset += len(page.get("features", []))
            log(f"   COOLR layer OK: {layer}")
            return records
        except RuntimeError as err:
            log(f"   COOLR layer unavailable: {layer} ({str(err)[:80]})")
    return None


def to_landslide(rec, source):
    """Normalise a NASA record to the landslides schema (section 12.2)."""
    def pick(*names):
        for n in names:
            if rec.get(n) not in (None, ""):
                return rec[n]
        return None

    date = pick("event_date")
    if isinstance(date, (int, float)):           # ArcGIS dates are epoch milliseconds
        date = datetime.fromtimestamp(date / 1000, timezone.utc).strftime("%Y-%m-%d")
    elif isinstance(date, str) and "/" in date:  # CSV dates: 08/01/2008 12:00:00 AM
        try:
            date = datetime.strptime(date.split()[0], "%m/%d/%Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    fat = pick("fatality_count")
    try:
        fat = int(float(fat)) if fat is not None else None
    except ValueError:
        fat = None
    return {
        "id": f"{source}_{pick('event_id', 'OBJECTID', 'objectid')}",
        "source": source,
        "event_date": date,
        "category": pick("landslide_category", "ls_cat"),
        "trigger": pick("landslide_trigger", "ls_trigger"),
        "fatalities": fat,
        "description": pick("event_title", "location_description"),
        "location_precision": pick("location_accuracy", "loc_acc"),
        "lon": float(rec["longitude"]),
        "lat": float(rec["latitude"]),
    }


def fetch_nasa_landslides(http, boundary):
    log("4. Landslides: NASA")
    bbox = boundary["bbox"]
    raw = fetch_nasa_coolr(http, bbox)
    source = "NASA_COOLR"
    if raw is None:
        warn("NASA COOLR ArcGIS services are offline; using the Global Landslide "
             "Catalog CSV export instead (events 2007-2017 only)")
        text = http.fetch(NASA_GLC_CSV, as_json=False, timeout=120)
        raw = []
        # io.StringIO (not splitlines) because some descriptions contain newlines
        for row in csv.DictReader(io.StringIO(text, newline="")):
            try:
                lon, lat = float(row["longitude"]), float(row["latitude"])
            except (KeyError, TypeError, ValueError):
                continue
            if bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]:
                raw.append(row)
        source = "NASA_GLC"

    landslides = []
    for rec in raw:
        try:
            ls = to_landslide(rec, source)
        except (KeyError, TypeError, ValueError):
            continue
        if point_in_geometry((ls["lon"], ls["lat"]), boundary["geometry"]):
            landslides.append(ls)
    log(f"   {len(raw)} in bbox -> {len(landslides)} inside the district")
    return landslides


def load_gsi_landslides(boundary):
    path = MANUAL_DIR / "gsi_landslides.geojson"
    if not path.exists():
        warn(f"{path.relative_to(ROOT)} not found - download the Landslide Inventory "
             "from GSI Bhukosh and export it to GeoJSON (EPSG:4326)")
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for i, f in enumerate(data.get("features", [])):
        c = centroid(f.get("geometry") or {})
        if c and point_in_geometry(c, boundary["geometry"]):
            props = f.get("properties") or {}
            out.append({"id": f"GSI_{i}", "source": "GSI", "event_date": None,
                        "category": None, "trigger": None, "fatalities": None,
                        "description": None, "location_precision": "gsi_inventory",
                        "lon": c[0], "lat": c[1], "gsi_properties": props})
    log(f"   GSI inventory: {len(out)} landslides")
    return out


def load_web_landslides(boundary):
    """Landslides collected from news reports (data/manual/web_landslides.csv).
    Each row is one reported event; rows we could not place on the map have
    an empty lat/lon and are skipped."""
    path = MANUAL_DIR / "web_landslides.csv"
    if not path.exists():
        warn(f"{path.relative_to(ROOT)} not found - news-based landslides skipped")
        return []
    out, skipped = [], 0
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                lat, lon = float(row["lat"]), float(row["lon"])
            except (KeyError, TypeError, ValueError):
                skipped += 1
                continue
            if not point_in_geometry((lon, lat), boundary["geometry"]):
                skipped += 1
                continue
            fat = row.get("fatalities")
            out.append({"id": f"NEWS_{row['id']}", "source": "NEWS",
                        "event_date": row.get("event_date") or None,
                        "category": row.get("type"), "trigger": "rainfall",
                        "fatalities": int(fat) if fat and fat.isdigit() else None,
                        "description": f"{row.get('place')}: {row.get('description')}",
                        "location_precision": row.get("location_precision"),
                        "source_url": row.get("source_url"), "lon": lon, "lat": lat})
    log(f"   news landslides: {len(out)} events ({skipped} not located)")
    return out


def susc_value_to_class(value):
    """Turn a susceptibility value ('High', 'Very High', 3, ...) into 1..4."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value) if 1 <= value <= 4 else None
    v = str(value).strip().lower()
    if v.isdigit():
        return int(v) if 1 <= int(v) <= 4 else None
    if "very" in v and "high" in v:
        return 4
    if "high" in v:
        return 3
    if "mod" in v or "medium" in v:
        return 2
    if "low" in v:
        return 1
    return None


def load_gsi_susceptibility():
    path = MANUAL_DIR / "gsi_susceptibility.geojson"
    if not path.exists():
        warn(f"{path.relative_to(ROOT)} not found - using the NASA global "
             "susceptibility map instead (lower weight)")
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    features = data.get("features", [])
    if not features:
        return []
    # auto-detect the class field: first key containing "susc" or "class"
    keys = list((features[0].get("properties") or {}).keys())
    field = next((k for k in keys if "susc" in k.lower()), None) or \
        next((k for k in keys if "class" in k.lower()), None)
    if field is None:
        warn(f"no susceptibility field found in {path.name} (keys: {keys})")
        return []
    zones = []
    for f in features:
        cls = susc_value_to_class((f.get("properties") or {}).get(field))
        g = f.get("geometry")
        if cls and g and g["type"] in ("Polygon", "MultiPolygon"):
            zones.append({"cls": cls, "geometry": g, "bbox": geometry_bbox(g)})
    log(f"   GSI susceptibility: {len(zones)} zones (field '{field}')")
    return zones


NASA_SUSC_TIF = ROOT / "data" / "raw" / "nasa_susceptibility" / \
    "global_landslide_susceptibility_2017.tif"
NASA_SUSC_URL = ("https://gpm.nasa.gov/sites/default/files/downloads/"
                 "global-landslide-susceptibility-map-2-27-23.tif")
# NASA uses 5 levels (1 very low .. 5 very high); we use GSI-style 1..4
NASA_TO_CLASS = {1: 1, 2: 1, 3: 2, 4: 3, 5: 4}


def load_nasa_susceptibility(http, boundary):
    """Fallback when there is no GSI file: NASA's global susceptibility map
    (Stanley & Kirschbaum 2017, ~1 km). Returns a function (lon, lat) -> 1..4,
    or None. Needs rasterio (optional; only this step uses it)."""
    try:
        import rasterio
        from rasterio.windows import from_bounds
    except ImportError:
        warn("rasterio not installed - NASA susceptibility skipped")
        return None
    if not NASA_SUSC_TIF.exists():
        log("   downloading NASA susceptibility map (33 MB)...")
        NASA_SUSC_TIF.parent.mkdir(parents=True, exist_ok=True)
        r = http.session.get(NASA_SUSC_URL, timeout=300)
        r.raise_for_status()
        NASA_SUSC_TIF.write_bytes(r.content)
    b = boundary["bbox"]
    with rasterio.open(NASA_SUSC_TIF) as src:
        win = from_bounds(b[0] - 0.05, b[1] - 0.05, b[2] + 0.05, b[3] + 0.05, src.transform)
        win = win.round_offsets().round_lengths()
        grid = src.read(1, window=win)
        transform = src.window_transform(win)
    inv = ~transform

    def lookup(lon, lat):
        col, row = inv * (lon, lat)
        row, col = int(row), int(col)
        if 0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]:
            return NASA_TO_CLASS.get(int(grid[row, col]))
        return None

    log(f"   NASA susceptibility: {grid.shape[1]}x{grid.shape[0]} cells (~1 km)")
    return lookup


def load_accidents():
    path = MANUAL_DIR / "accidents.csv"
    if not path.exists():
        warn(f"{path.relative_to(ROOT)} not found - start it from "
             "data/manual/accidents.example.csv (accident factor skipped)")
        return []
    accidents = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                row["lat"], row["lon"] = float(row["lat"]), float(row["lon"])
            except (KeyError, ValueError):
                warn(f"accidents.csv: skipping row with bad lat/lon: {row.get('id')}")
                continue
            row["type"] = (row.get("type") or "accident").strip().lower()
            row["severity"] = (row.get("severity") or "unknown").strip().lower()
            accidents.append(row)
    log(f"   accidents.csv: {len(accidents)} rows")
    return accidents


# --------------------------------------------------------------------------- #
# 6. Weather
# --------------------------------------------------------------------------- #

def rain_factor(next24, past72):
    """Section 10.5 table."""
    if next24 > 65 or past72 > 150:
        return 1.0
    if next24 > 35 or past72 > 75:
        return 0.6
    if next24 >= 10 or past72 >= 30:
        return 0.3
    return 0.0


def fetch_weather(http):
    log("6. Weather: Open-Meteo for the key towns")
    data = http.fetch(OPEN_METEO_FORECAST, params={
        "latitude": ",".join(str(t[1]) for t in TOWNS),
        "longitude": ",".join(str(t[2]) for t in TOWNS),
        "hourly": "precipitation,rain,snowfall,visibility,weather_code",
        "daily": "precipitation_sum,rain_sum,snowfall_sum",
        "current": "precipitation,weather_code",
        "past_days": 3, "forecast_days": 3, "timezone": "Asia/Kolkata"})
    if isinstance(data, dict):
        data = [data]

    out = []
    for (name, lat, lon), loc in zip(TOWNS, data):
        hourly = loc["hourly"]
        now = datetime.fromisoformat(loc["current"]["time"])
        past72 = next24 = snow24 = 0.0
        vis24 = []
        for i, t in enumerate(hourly["time"]):
            t = datetime.fromisoformat(t)
            precip = hourly["precipitation"][i] or 0.0
            if now - timedelta(hours=72) <= t < now:
                past72 += precip
            elif now <= t < now + timedelta(hours=24):
                next24 += precip
                snow24 += hourly["snowfall"][i] or 0.0
                if hourly["visibility"][i] is not None:
                    vis24.append(hourly["visibility"][i])
        out.append({
            "point_id": name.lower(), "name": name, "lat": lat, "lon": lon,
            "fetched_at": datetime.now(IST).isoformat(timespec="seconds"),
            "rain_past_72h_mm": round(past72, 1),
            "rain_next_24h_mm": round(next24, 1),
            "snow_next_24h_cm": round(snow24, 1),
            "min_visibility_m": min(vis24) if vis24 else None,
            "weather_code_now": loc["current"].get("weather_code"),
            "rain_factor": rain_factor(next24, past72),
        })
    log("   " + ", ".join(f"{w['name']} {w['rain_next_24h_mm']}mm" for w in out))
    return out


# --------------------------------------------------------------------------- #
# 7. Segmentation
# --------------------------------------------------------------------------- #

def segment_roads(ways, max_len):
    """Split each way at junctions (nodes shared with other ways) and then into
    pieces of at most ~max_len metres. Cuts happen only at existing vertices, so
    every segment starts and ends on a real OSM node (needed for the graph)."""
    log(f"7. Segmentation: <= {max_len} m")
    node_count = Counter()
    for w in ways:
        node_count.update(set(w["nodes"]))
        node_count[w["nodes"][0]] += 1      # way ends are always graph nodes
        node_count[w["nodes"][-1]] += 1
    junctions = {n for n, c in node_count.items() if c > 1}

    segments = []
    for w in ways:
        coords, nodes = w["coords"], w["nodes"]
        # step 1: cut at junctions
        cut_points = [0] + [i for i in range(1, len(nodes) - 1) if nodes[i] in junctions] \
            + [len(nodes) - 1]
        pieces = []
        for a, b in zip(cut_points, cut_points[1:]):
            # step 2: cut long pieces at vertices
            start, run = a, 0.0
            for i in range(a + 1, b + 1):
                d = haversine(coords[i - 1], coords[i])
                if run + d > max_len and i - 1 > start:
                    pieces.append((start, i - 1))
                    start, run = i - 1, 0.0
                run += d
            pieces.append((start, b))

        for k, (a, b) in enumerate(pieces):
            seg_coords = coords[a:b + 1]
            segments.append({
                "segment_id": f"w{w['osm_id']}_s{k:03d}",
                "osm_way_id": w["osm_id"],
                "u_node": nodes[a], "v_node": nodes[b],
                "highway": w["highway"], "name": w["name"], "ref": w["ref"],
                "surface": w["surface"], "lanes": w["lanes"], "width": w["width"],
                "oneway": w["oneway"], "bridge": w["bridge"], "tunnel": w["tunnel"],
                "length_m": round(line_length(seg_coords), 1),
                "coords": seg_coords,
            })
    log(f"   {len(ways)} ways -> {len(segments)} segments")
    return segments


def base_class(highway):
    return (highway or "").replace("_link", "")


# --------------------------------------------------------------------------- #
# 8. Elevation
# --------------------------------------------------------------------------- #

CROSS_OFFSET_M = 100   # sample the hillside 100 m either side of the road


class TerrainTiles:
    """Elevation from the free AWS "Terrain Tiles" (Terrarium PNG format).
    At zoom 12 one pixel is ~33 m in Chamoli (SRTM-based). The tiles are
    cached in cache/ like every other download, so a re-run is instant.
    Decoding: elevation_m = R * 256 + G + B / 256 - 32768."""

    URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"

    def __init__(self, http, zoom=12):
        from PIL import Image      # imported here so Pillow is only needed for this source
        self.Image = Image
        self.http, self.zoom, self.tiles = http, zoom, {}

    def _tile(self, x, y):
        if (x, y) not in self.tiles:
            png = self.http.fetch(self.URL.format(z=self.zoom, x=x, y=y), binary=True)
            self.tiles[(x, y)] = self.Image.open(io.BytesIO(png)).convert("RGB").load()
        return self.tiles[(x, y)]

    def elevation(self, lon, lat):
        # standard Web-Mercator "slippy map" tile maths
        n = 2 ** self.zoom
        fx = (lon + 180) / 360 * n
        fy = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
        tx, ty = int(fx), int(fy)
        px, py = min(int((fx - tx) * 256), 255), min(int((fy - ty) * 256), 255)
        r, g, b = self._tile(tx, ty)[px, py]
        return round(r * 256 + g + b / 256 - 32768, 1)


def elevations_from_tiles(http, keys):
    tiles = TerrainTiles(http)
    elev = {}
    for i, k in enumerate(keys):
        try:
            elev[k] = tiles.elevation(*k)
        except RuntimeError as err:
            warn(f"terrain tile failed at {k}: {err}")
        if i % 5000 == 4999:
            log(f"   {i + 1}/{len(keys)} points ({len(tiles.tiles)} tiles)")
    log(f"   {len(tiles.tiles)} terrain tiles used")
    return elev


def elevations_from_open_meteo(http, keys):
    """Open-Meteo counts every point as one API call (600/min, ~10,000/day on
    the free tier), so we send 100 points every 10 s to stay under the limit."""
    elev = {}
    for i in range(0, len(keys), 100):
        batch = keys[i:i + 100]
        try:
            res = http.fetch(OPEN_METEO_ELEVATION, params={
                "latitude": ",".join(f"{k[1]:.4f}" for k in batch),
                "longitude": ",".join(f"{k[0]:.4f}" for k in batch)})
            elev.update(zip(batch, res["elevation"]))
        except RuntimeError as err:
            warn(f"elevation batch {i // 100} failed: {err}")
        log(f"   {min(i + 100, len(keys))}/{len(keys)} points")
        if i + 100 < len(keys):
            time.sleep(10)
    return elev


def add_elevation(http, segments, source, max_points):
    """Sample start / mid / end of each segment (road gradient) and two points
    100 m to either side of the midpoint (terrain steepness across the road).
    This is a point-sampling proxy - the 30 m slope raster from QGIS
    (zonal statistics in a 50 m buffer) replaces it in phase 2."""
    if source == "tiles":
        try:
            import PIL  # noqa: F401
        except ImportError:
            warn("Pillow not installed - falling back to the Open-Meteo elevation API")
            source = "open-meteo"
    budget = math.inf if source == "tiles" else max_points
    log(f"8. Elevation: {source}" + ("" if source == "tiles" else f" (max {max_points} points)"))

    def key(p):
        return (round(p[0], 4), round(p[1], 4))

    # main roads first, so a limited budget is spent where it matters
    order = sorted(segments, key=lambda s: (CLASS_RANK.get(base_class(s["highway"]), 99),
                                            s["segment_id"]))
    wanted, plan = {}, {}
    for s in order:
        mid, b = point_along(s["coords"], 0.5)
        pts = {"start": s["coords"][0], "mid": mid, "end": s["coords"][-1],
               "left": offset_point(mid, b - 90, CROSS_OFFSET_M),
               "right": offset_point(mid, b + 90, CROSS_OFFSET_M)}
        new_keys = {key(p) for p in pts.values()} - wanted.keys()
        if len(wanted) + len(new_keys) > budget:
            continue
        for p in pts.values():
            wanted.setdefault(key(p), p)
        plan[s["segment_id"]] = {k: key(p) for k, p in pts.items()}

    keys = list(wanted)
    if source == "tiles":
        elev = elevations_from_tiles(http, keys)
    else:
        elev = elevations_from_open_meteo(http, keys)

    done = 0
    for s in segments:
        p = plan.get(s["segment_id"])
        e = {k: elev.get(v) for k, v in p.items()} if p else {}
        if not e or None in (e["start"], e["mid"], e["end"]):
            s.update({"elev_start_m": None, "elev_end_m": None, "elev_min_m": None,
                      "elev_max_m": None, "gradient_avg_pct": None,
                      "gradient_max_pct": None, "cross_slope_deg": None})
            continue
        done += 1
        length = max(s["length_m"], 1.0)
        profile = [e["start"], e["mid"], e["end"]]
        s["elev_start_m"], s["elev_end_m"] = e["start"], e["end"]
        s["elev_min_m"], s["elev_max_m"] = min(profile), max(profile)
        s["gradient_avg_pct"] = round(abs(e["end"] - e["start"]) / length * 100, 2)
        s["gradient_max_pct"] = round(max(abs(e["mid"] - e["start"]),
                                          abs(e["end"] - e["mid"])) / (length / 2) * 100, 2)
        if e["left"] is not None and e["right"] is not None:
            s["cross_slope_deg"] = round(math.degrees(math.atan(
                abs(e["left"] - e["right"]) / (2 * CROSS_OFFSET_M))), 1)
        else:
            s["cross_slope_deg"] = None
    if done < len(segments):
        warn(f"elevation sampled for {done}/{len(segments)} segments"
             + (" (raise --max-elev-points to cover more)" if source != "tiles" else ""))
    log(f"   {len(keys)} points, {done} segments with elevation")


# --------------------------------------------------------------------------- #
# 9. Geometry attributes
# --------------------------------------------------------------------------- #

def add_geometry_attributes(segments, min_vertex_gap=10, sharp_deg=60):
    log("9. Curvature and sharp turns")
    for s in segments:
        # drop vertices closer than 10 m so GPS noise doesn't look like bends
        pts = [s["coords"][0]]
        for p in s["coords"][1:]:
            if haversine(pts[-1], p) >= min_vertex_gap:
                pts.append(p)
        total_turn, sharp = 0.0, 0
        for i in range(1, len(pts) - 1):
            turn = abs(bearing(pts[i], pts[i + 1]) - bearing(pts[i - 1], pts[i]))
            turn = min(turn, 360 - turn)
            total_turn += turn
            if turn > sharp_deg:
                sharp += 1
        km = max(s["length_m"], 1.0) / 1000
        s["curvature_deg_per_km"] = round(total_turn / km, 1)
        s["sharp_turns"] = sharp


# --------------------------------------------------------------------------- #
# 10. Proximity attributes
# --------------------------------------------------------------------------- #

def add_proximity_attributes(segments, landslides, accidents, pois, weather, susc_zones,
                             nasa_susc=None):
    log("10. Proximity: landslides, accidents, hospitals, weather, susceptibility")
    proj = LocalProjection(30.4)
    hospitals = [p for p in pois if p["category"] in ("hospital", "clinic")]

    def prep(points):
        return [(proj((p["lon"], p["lat"])), p) for p in points]

    precise = [l for l in landslides if l.get("location_precision") in PRECISE_LOCATIONS]
    log(f"   using {len(precise)}/{len(landslides)} landslides with location accuracy <= 10 km")
    ls_xy, acc_xy, hosp_xy = prep(precise), prep(accidents), prep(hospitals)

    for s in segments:
        line = [proj(c) for c in s["coords"]]
        xs, ys = [p[0] for p in line], [p[1] for p in line]
        box = (min(xs), min(ys), max(xs), max(ys))

        def box_dist(pt):
            dx = max(box[0] - pt[0], 0, pt[0] - box[2])
            dy = max(box[1] - pt[1], 0, pt[1] - box[3])
            return math.hypot(dx, dy)

        def nearest(items):
            best = math.inf
            for xy, _ in items:
                if box_dist(xy) < best:      # cheap lower bound first
                    best = min(best, point_line_dist(xy, line))
            return None if best == math.inf else round(best, 1)

        def within(items, radius):
            return [p for xy, p in items
                    if box_dist(xy) <= radius and point_line_dist(xy, line) <= radius]

        s["landslides_within_500m"] = len(within(ls_xy, 500))
        s["nearest_landslide_m"] = nearest(ls_xy)

        near_acc = within(acc_xy, 500)
        s["accidents_within_500m"] = float(sum(
            SEVERITY_WEIGHT.get(a["severity"], 1) for a in near_acc if a["type"] == "accident"))
        s["is_black_spot"] = any(a["type"] == "black_spot" for a in within(acc_xy, 250))

        s["nearest_hospital_m"] = nearest(hosp_xy)

        mid, _ = point_along(s["coords"], 0.5)
        s["nearest_weather_point"] = min(
            weather, key=lambda w: haversine(mid, (w["lon"], w["lat"])))["point_id"] \
            if weather else None

        # susceptibility: highest class among start / mid / end
        cls = None
        for p in (s["coords"][0], mid, s["coords"][-1]):
            for z in susc_zones:
                b = z["bbox"]
                if b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3] and \
                        point_in_geometry(p, z["geometry"]):
                    cls = max(cls or 0, z["cls"])
        source = "GSI" if cls else None
        # no GSI zone here -> fall back to the NASA global map
        if cls is None and nasa_susc:
            vals = [v for v in (nasa_susc(*p) for p in
                                (s["coords"][0], mid, s["coords"][-1])) if v]
            if vals:
                cls, source = max(vals), "NASA"
        s["landslide_susc_class"] = cls
        s["susc_source"] = source


# --------------------------------------------------------------------------- #
# 10b. River attributes
# --------------------------------------------------------------------------- #

def segments_intersect(a, b, c, d):
    """Do line pieces a-b and c-d cross? (orientation test, projected metres)"""
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2 = orient(c, d, a), orient(c, d, b)
    d3, d4 = orient(a, b, c), orient(a, b, d)
    return (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0)


def piece_piece_dist(a, b, c, d):
    """Shortest distance between line pieces a-b and c-d."""
    if segments_intersect(a, b, c, d):
        return 0.0
    return min(point_segment_dist(a, c, d), point_segment_dist(b, c, d),
               point_segment_dist(c, a, b), point_segment_dist(d, a, b))


class PieceGrid:
    """Very small spatial index: every straight piece of every line is put in
    the 1 km grid cells its bounding box touches, so we only compare a road
    segment with river pieces that are nearby instead of all of them."""

    def __init__(self, lines_xy, cell=1000.0):
        self.cell = cell
        self.cells = defaultdict(list)
        for line_id, xy in lines_xy:
            for i in range(len(xy) - 1):
                a, b = xy[i], xy[i + 1]
                for cx in range(int(min(a[0], b[0]) // cell), int(max(a[0], b[0]) // cell) + 1):
                    for cy in range(int(min(a[1], b[1]) // cell),
                                    int(max(a[1], b[1]) // cell) + 1):
                        self.cells[(cx, cy)].append((line_id, a, b))

    def pieces_near(self, box, rings=0):
        """Pieces in the cells covering box (xmin, ymin, xmax, ymax) plus `rings` extra cells."""
        x0, y0 = int(box[0] // self.cell) - rings, int(box[1] // self.cell) - rings
        x1, y1 = int(box[2] // self.cell) + rings, int(box[3] // self.cell) + rings
        seen = set()
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                for piece in self.cells.get((cx, cy), ()):
                    if id(piece) not in seen:
                        seen.add(id(piece))
                        yield piece


def add_river_attributes(segments, rivers, max_search_km=20):
    """dist_to_river_m: distance from the segment to the nearest river
    (rivers cut the toe of the slope -> more landslides on riverside roads).
    stream_crossings: how many streams/nalas cross the segment (debris flows
    and washed-out culverts happen at these crossings in the monsoon)."""
    log("10b. Rivers: distance to river, stream crossings")
    proj = LocalProjection(30.4)
    river_grid = PieceGrid([(r["osm_id"], [proj(c) for c in r["coords"]])
                            for r in rivers if r["kind"] == "river"])
    stream_grid = PieceGrid([(r["osm_id"], [proj(c) for c in r["coords"]])
                             for r in rivers if r["kind"] == "stream"])
    max_rings = int(max_search_km * 1000 // river_grid.cell)

    for s in segments:
        line = [proj(c) for c in s["coords"]]
        box = (min(p[0] for p in line), min(p[1] for p in line),
               max(p[0] for p in line), max(p[1] for p in line))
        road_pieces = list(zip(line, line[1:]))

        # nearest river: widen the search one ring of cells at a time; once the
        # best distance found is smaller than the ring radius we can stop
        best = math.inf
        for rings in range(max_rings + 1):
            for _, c, d in river_grid.pieces_near(box, rings):
                for a, b in road_pieces:
                    best = min(best, piece_piece_dist(a, b, c, d))
            if best <= rings * river_grid.cell:
                break
        s["dist_to_river_m"] = None if best == math.inf else round(best, 1)

        crossed = {sid for sid, c, d in stream_grid.pieces_near(box)
                   if any(segments_intersect(a, b, c, d) for a, b in road_pieces)}
        s["stream_crossings"] = len(crossed)


def rivers_report(rivers, segments):
    """Numbers for the summary JSON."""
    by_name = defaultdict(float)
    for r in rivers:
        if r["kind"] == "river":
            by_name[r["name"] or "(unnamed)"] += r["length_m"] / 1000
    report = {
        "river_ways": sum(1 for r in rivers if r["kind"] == "river"),
        "stream_ways": sum(1 for r in rivers if r["kind"] == "stream"),
        "river_km": round(sum(r["length_m"] for r in rivers if r["kind"] == "river") / 1000, 1),
        "stream_km": round(sum(r["length_m"] for r in rivers if r["kind"] == "stream") / 1000, 1),
        "rivers_by_name_km": {k: round(v, 1) for k, v in
                              sorted(by_name.items(), key=lambda kv: -kv[1])[:12]},
    }
    if segments and "dist_to_river_m" in segments[0]:
        def km_within(m):
            return round(sum(s["length_m"] for s in segments
                             if s["dist_to_river_m"] is not None
                             and s["dist_to_river_m"] <= m) / 1000, 1)
        report["road_km_within_100m_of_river"] = km_within(100)
        report["road_km_within_250m_of_river"] = km_within(250)
        report["road_km_within_500m_of_river"] = km_within(500)
        report["segments_with_stream_crossings"] = sum(
            1 for s in segments if s["stream_crossings"])
        report["total_stream_crossings"] = sum(s["stream_crossings"] for s in segments)
    return report


# --------------------------------------------------------------------------- #
# 11. Preview risk
# --------------------------------------------------------------------------- #

def risk_class(r):
    if r < 0.25:
        return "low"
    if r < 0.5:
        return "medium"
    if r < 0.75:
        return "high"
    return "very_high"


def add_static_risk(segments, have_landslides, have_accidents, have_susc):
    """Weighted sum of normalised factors (section 10.3/10.4). Factors without
    data are left out and their weight is shared out among the others."""
    log("11. Preview static risk")
    for s in segments:
        f = {}
        if have_susc and s["landslide_susc_class"]:
            f["susceptibility"] = SUSC_SCORE[s["landslide_susc_class"]]
        if have_landslides:
            f["landslide_density"] = min(s["landslides_within_500m"] / 5, 1)
        # terrain slope: cross-road slope if sampled, else road gradient as a proxy
        if s.get("cross_slope_deg") is not None:
            f["terrain_slope"] = min(s["cross_slope_deg"] / 45, 1)
        elif s.get("gradient_avg_pct") is not None:
            f["terrain_slope"] = min(s["gradient_avg_pct"] / 12, 1)
        f["curvature"] = min(s["curvature_deg_per_km"] / 1500, 1)
        if have_accidents:
            acc = min(s["accidents_within_500m"] / 5, 1)
            f["accident_density"] = max(acc, 0.8) if s["is_black_spot"] else acc

        weights = dict(RISK_WEIGHTS)
        if s.get("susc_source") == "NASA":
            weights["susceptibility"] = NASA_SUSC_WEIGHT
        total_w = sum(weights[k] for k in f)
        risk = sum(weights[k] * v for k, v in f.items()) / total_w
        s["static_risk"] = round(risk, 3)
        s["risk_class"] = risk_class(risk)
        s["risk_factors"] = {k: round(v, 3) for k, v in f.items()}
        s["dynamic"] = 1.0
        s["risk_now"] = s["static_risk"]
        s["closed"] = False


# --------------------------------------------------------------------------- #
# 12. Optional: TomTom incidents, OpenTopography DEM
# --------------------------------------------------------------------------- #

def bbox_tiles(bbox, max_km2=9000):
    """Split a bbox into a grid of tiles each smaller than max_km2 (TomTom limit 10,000)."""
    w = haversine((bbox[0], bbox[1]), (bbox[2], bbox[1])) / 1000
    h = haversine((bbox[0], bbox[1]), (bbox[0], bbox[3])) / 1000
    n = 1
    while (w / n) * (h / n) > max_km2:
        n += 1
    dx, dy = (bbox[2] - bbox[0]) / n, (bbox[3] - bbox[1]) / n
    return [[bbox[0] + i * dx, bbox[1] + j * dy, bbox[0] + (i + 1) * dx, bbox[1] + (j + 1) * dy]
            for i in range(n) for j in range(n)]


def fetch_incidents(http, boundary):
    key = os.environ.get("TOMTOM_API_KEY")
    if not key:
        log("12a. Incidents: skipped (no TOMTOM_API_KEY)")
        return {"enabled": False, "count": 0, "items": []}
    log("12a. Incidents: TomTom")
    fields = ("{incidents{type,geometry{type,coordinates},properties{id,iconCategory,"
              "magnitudeOfDelay,events{description,code},startTime,endTime,from,to,"
              "length,delay,roadNumbers}}}")
    items = {}
    for tile in bbox_tiles(boundary["bbox"]):
        try:
            res = http.fetch("https://api.tomtom.com/traffic/services/5/incidentDetails",
                             params={"key": key, "bbox": ",".join(f"{v:.4f}" for v in tile),
                                     "fields": fields, "language": "en-GB",
                                     "timeValidityFilter": "present"})
            for inc in res.get("incidents", []):
                items[inc["properties"]["id"]] = inc
        except RuntimeError as err:
            warn(f"TomTom tile failed: {err}")
    log(f"   {len(items)} incidents")
    return {"enabled": True, "count": len(items), "items": list(items.values())}


def fetch_dem(http, boundary, out_dir):
    key = os.environ.get("OPENTOPO_API_KEY")
    if not key:
        warn("OPENTOPO_API_KEY not set - Copernicus 30 m DEM not downloaded "
             "(get a free key at portal.opentopography.org)")
        return None
    log("12b. DEM: OpenTopography COP30")
    b = boundary["bbox"]
    tif = http.fetch("https://portal.opentopography.org/API/globaldem", binary=True,
                     timeout=600, params={"demtype": "COP30", "south": b[1], "north": b[3],
                                          "west": b[0], "east": b[2],
                                          "outputFormat": "GTiff", "API_Key": key})
    path = out_dir / "dem_cop30.tif"
    path.write_bytes(tif)
    log(f"   saved {path} ({len(tif) / 1e6:.1f} MB)")
    return str(path.relative_to(ROOT))


# --------------------------------------------------------------------------- #
# 13. Output + sanity checks
# --------------------------------------------------------------------------- #

SEGMENT_FIELDS = [
    "segment_id", "osm_way_id", "u_node", "v_node", "highway", "name", "ref",
    "surface", "lanes", "width", "oneway", "bridge", "tunnel", "length_m",
    "elev_start_m", "elev_end_m", "elev_min_m", "elev_max_m", "gradient_avg_pct",
    "gradient_max_pct", "cross_slope_deg", "curvature_deg_per_km", "sharp_turns",
    "landslide_susc_class", "susc_source", "landslides_within_500m", "nearest_landslide_m",
    "accidents_within_500m", "is_black_spot", "dist_to_river_m", "stream_crossings",
    "nearest_hospital_m",
    "nearest_weather_point", "static_risk", "risk_class", "dynamic", "risk_now", "closed",
]


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def is_nh7(seg):
    ref = (seg.get("ref") or "").upper()
    return bool(re.search(r"NH\s*-?\s*7\b", ref)) or "badrinath" in (seg.get("name") or "").lower()


def nh7_continuity(segments):
    """Is there an unbroken NH-7 path from Karnaprayag to Badrinath?"""
    nh = [s for s in segments if is_nh7(s)]
    if not nh:
        return {"found": False}
    graph = defaultdict(set)
    node_pos = {}
    for s in nh:
        graph[s["u_node"]].add(s["v_node"])
        graph[s["v_node"]].add(s["u_node"])
        node_pos[s["u_node"]], node_pos[s["v_node"]] = s["coords"][0], s["coords"][-1]

    def closest(town):
        lat, lon = next((t[1], t[2]) for t in TOWNS if t[0] == town)
        n = min(node_pos, key=lambda k: haversine(node_pos[k], (lon, lat)))
        return n, haversine(node_pos[n], (lon, lat))

    start, d_start = closest("Karnaprayag")
    goal, d_goal = closest("Badrinath")
    seen, queue = {start}, deque([start])
    while queue:
        n = queue.popleft()
        for m in graph[n]:
            if m not in seen:
                seen.add(m)
                queue.append(m)
    return {"found": True, "km": round(sum(s["length_m"] for s in nh) / 1000, 1),
            "continuous_karnaprayag_to_badrinath": goal in seen,
            "start_node_dist_m": round(d_start), "end_node_dist_m": round(d_goal)}


def sanity_checks(boundary, segments, landslides, weather):
    checks = {}
    b, e = boundary["bbox"], EXPECTED_BBOX
    checks["area_km2"] = {"value": boundary["area_km2"], "expected": "~7,700",
                          "ok": 0.8 * EXPECTED_AREA_KM2 <= boundary["area_km2"]
                          <= 1.2 * EXPECTED_AREA_KM2}
    tol = 0.05   # the expected bbox in the brief is itself approximate
    checks["bbox_inside_expected"] = (b[0] >= e[0] - tol and b[1] >= e[1] - tol
                                      and b[2] <= e[2] + tol and b[3] <= e[3] + tol)
    if segments:
        km = sum(s["length_m"] for s in segments) / 1000
        checks["total_road_km"] = {"value": round(km), "ok": 200 <= km <= 10000}
        checks["nh7"] = nh7_continuity(segments)

        def town_elev(name):
            lat, lon = next((t[1], t[2]) for t in TOWNS if t[0] == name)
            near = [s for s in segments if s.get("elev_start_m") is not None]
            if not near:
                return None
            s = min(near, key=lambda s: haversine(s["coords"][0], (lon, lat)))
            return s["elev_start_m"]

        checks["elevation_m"] = {"Karnaprayag": town_elev("Karnaprayag"),
                                 "Badrinath": town_elev("Badrinath"),
                                 "expected": "Karnaprayag ~700-900, Badrinath ~3,100"}
    if landslides:
        towns = Counter()
        for ls in landslides:
            t = min(TOWNS, key=lambda t: haversine((ls["lon"], ls["lat"]), (t[2], t[1])))
            towns[t[0]] += 1
        checks["landslides_nearest_town"] = dict(towns.most_common())
    if weather:
        checks["weather_non_negative"] = all(
            w["rain_past_72h_mm"] >= 0 and w["rain_next_24h_mm"] >= 0 for w in weather)
    return checks


def build_outputs(args, out_dir, boundary, segments, ways, landslides, accidents,
                  pois, rivers, weather, incidents, dem_path):
    out_dir.mkdir(parents=True, exist_ok=True)

    write_json(out_dir / "boundary.geojson", feature_collection([{
        "type": "Feature", "geometry": boundary["geometry"],
        "properties": {k: v for k, v in boundary.items() if k != "geometry"}}]))

    if segments:
        write_json(out_dir / "roads_segments.geojson", feature_collection([
            feature("LineString", [[round(x, 6), round(y, 6)] for x, y in s["coords"]],
                    {k: s.get(k) for k in SEGMENT_FIELDS + ["risk_factors"]})
            for s in segments]))
        with open(out_dir / "segments.csv", "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=SEGMENT_FIELDS + ["wkt"])
            writer.writeheader()
            for s in segments:
                row = {k: s.get(k) for k in SEGMENT_FIELDS}
                row["wkt"] = "LINESTRING (" + ", ".join(
                    f"{x:.6f} {y:.6f}" for x, y in s["coords"]) + ")"
                writer.writerow(row)

    write_json(out_dir / "landslides.geojson", feature_collection([
        feature("Point", [l["lon"], l["lat"]],
                {k: v for k, v in l.items() if k not in ("lon", "lat")})
        for l in landslides]))
    write_json(out_dir / "accidents.geojson", feature_collection([
        feature("Point", [a["lon"], a["lat"]],
                {k: v for k, v in a.items() if k not in ("lon", "lat")})
        for a in accidents]))
    write_json(out_dir / "pois.geojson", feature_collection([
        feature("Point", [p["lon"], p["lat"]],
                {k: v for k, v in p.items() if k not in ("lon", "lat")})
        for p in pois]))
    if rivers:
        write_json(out_dir / "rivers.geojson", feature_collection([
            feature("LineString", [[round(x, 6), round(y, 6)] for x, y in r["coords"]],
                    {k: v for k, v in r.items() if k != "coords"})
            for r in rivers]))
    write_json(out_dir / "weather.json", weather)
    if incidents["enabled"]:
        write_json(out_dir / "incidents.json", incidents["items"])

    # ---- summary ----
    by_class_km = defaultdict(float)
    for s in segments:
        by_class_km[base_class(s["highway"])] += s["length_m"] / 1000
    risk_km = defaultdict(float)
    for s in segments:
        risk_km[s["risk_class"]] += s["length_m"] / 1000
    top = sorted(segments, key=lambda s: -s["static_risk"])[:10]

    summary = {
        "generated_at": datetime.now(IST).isoformat(timespec="seconds"),
        "study_area": {k: boundary[k] for k in
                       ("name", "osm_relation_id", "bbox", "area_km2")},
        "datasets": {
            "roads": {"ways": len(ways), "segments": len(segments),
                      "total_km": round(sum(s["length_m"] for s in segments) / 1000, 1),
                      "by_class_km": {k: round(v, 1) for k, v in
                                      sorted(by_class_km.items(), key=lambda kv: -kv[1])}},
            "landslides": {
                "nasa": sum(1 for l in landslides if l["source"].startswith("NASA")),
                "news": sum(1 for l in landslides if l["source"] == "NEWS"),
                "gsi": sum(1 for l in landslides if l["source"] == "GSI"),
                "sample": [{k: l[k] for k in ("event_date", "description", "lon", "lat")}
                           for l in landslides[:5]]},
            "accidents": {"count": sum(1 for a in accidents if a["type"] == "accident"),
                          "black_spots": sum(1 for a in accidents if a["type"] == "black_spot")},
            "pois": dict(Counter(p["category"] for p in pois)),
            "rivers": rivers_report(rivers, segments) if rivers else None,
            "weather": [{k: w[k] for k in ("name", "rain_past_72h_mm", "rain_next_24h_mm",
                                           "snow_next_24h_cm", "rain_factor")}
                        for w in weather],
            "incidents": {"enabled": incidents["enabled"], "count": incidents["count"]},
            "dem": dem_path,
        },
        "risk_preview": {
            "note": "preview only - weights from section 10.4, factors without data skipped",
            "by_class_km": {c: round(risk_km.get(c, 0), 1)
                            for c in ("low", "medium", "high", "very_high")},
            "top_10_segments": [{
                "segment_id": s["segment_id"], "name": s["name"], "ref": s["ref"],
                "highway": s["highway"], "static_risk": s["static_risk"],
                "factors": s["risk_factors"],
                "mid_lonlat": [round(v, 5) for v in point_along(s["coords"], 0.5)[0]]}
                for s in top],
        } if segments else None,
        "sanity_checks": sanity_checks(boundary, segments, landslides, weather),
        "warnings": WARNINGS,
    }
    write_json(out_dir / "summary.json", summary)
    return summary


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

STEPS = ["boundary", "roads", "pois", "places", "rivers", "landslides", "weather", "elevation",
         "incidents", "dem", "manual"]


def parse_args():
    p = argparse.ArgumentParser(description="Fetch and pre-process SafeYatra data for Chamoli.")
    p.add_argument("--only", help="comma list of steps: " + ",".join(STEPS))
    p.add_argument("--segment-length", type=float, default=500, help="max segment length (m)")
    p.add_argument("--road-classes", choices=["main", "all"], default="all")
    p.add_argument("--elev-source", choices=["tiles", "open-meteo"], default="tiles",
                   help="tiles = AWS Terrain Tiles (~30 m, no limit); "
                        "open-meteo = elevation API (~90 m, rate limited)")
    p.add_argument("--max-elev-points", type=int, default=5000,
                   help="point budget for --elev-source open-meteo")
    p.add_argument("--full", action="store_true", help="print full summary JSON")
    p.add_argument("--refresh", action="store_true", help="ignore the cache")
    p.add_argument("--out", default=str(ROOT / "output"))
    args = p.parse_args()
    args.steps = set(STEPS) if not args.only else {s.strip() for s in args.only.split(",")}
    unknown = args.steps - set(STEPS)
    if unknown:
        p.error(f"unknown step(s): {', '.join(sorted(unknown))}")
    return args


def main():
    load_dotenv(ROOT / ".env")
    args = parse_args()
    http = Http(refresh=args.refresh)
    out_dir = Path(args.out)
    steps = args.steps

    boundary = fetch_boundary(http)   # always needed: every other step uses it

    ways = fetch_roads(http, boundary, args.road_classes) if "roads" in steps else []
    pois = fetch_pois(http, boundary) if "pois" in steps else []
    places = fetch_places(http, boundary) if "places" in steps else []
    rivers = fetch_rivers(http, boundary) if "rivers" in steps else []

    landslides = []
    if "landslides" in steps:
        try:
            landslides = fetch_nasa_landslides(http, boundary)
        except RuntimeError as err:
            warn(f"NASA landslides failed: {err}")
    susc_zones, accidents = [], []
    if "manual" in steps:
        log("5. Manual datasets")
        landslides += load_web_landslides(boundary)
        landslides += load_gsi_landslides(boundary)
        susc_zones = load_gsi_susceptibility()
        accidents = load_accidents()
    nasa_susc = None
    if "manual" in steps and not susc_zones:
        nasa_susc = load_nasa_susceptibility(http, boundary)

    weather = []
    if "weather" in steps:
        try:
            weather = fetch_weather(http)
        except RuntimeError as err:
            warn(f"weather failed: {err}")

    segments = segment_roads(ways, args.segment_length) if ways else []
    if segments:
        if "elevation" in steps:
            add_elevation(http, segments, args.elev_source, args.max_elev_points)
        add_geometry_attributes(segments)
        add_proximity_attributes(segments, landslides, accidents, pois, weather, susc_zones,
                                 nasa_susc)
        if rivers:
            add_river_attributes(segments, rivers)
        add_static_risk(segments, have_landslides=bool(landslides),
                        have_accidents=bool(accidents),
                        have_susc=bool(susc_zones) or nasa_susc is not None)

    incidents = fetch_incidents(http, boundary) if "incidents" in steps else \
        {"enabled": False, "count": 0, "items": []}
    out_dir.mkdir(parents=True, exist_ok=True)
    dem_path = fetch_dem(http, boundary, out_dir) if "dem" in steps else None

    log("13. Writing output files")
    if places:
        write_json(out_dir / "places.json", places)
    summary = build_outputs(args, out_dir, boundary, segments, ways, landslides, accidents,
                            pois, rivers, weather, incidents, dem_path)
    if not args.full and summary.get("risk_preview"):
        summary["risk_preview"]["top_10_segments"] = summary["risk_preview"]["top_10_segments"][:5]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    log(f"Done. Files written to {out_dir}")


if __name__ == "__main__":
    main()
