"""
Weather for the 10 key towns from Open-Meteo (free, no key), refreshed hourly.

Because it is often dry (e.g. November = 0 mm everywhere), the admin can switch
on a demo SCENARIO ("moderate" / "heavy" monsoon day) to show how rain changes
risk and routes. Scenario values are clearly flagged as simulated in the API.
"""

from datetime import datetime, timedelta, timezone

import httpx

from .config import USER_AGENT
from .risk import rain_factor

OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
IST = timezone(timedelta(hours=5, minutes=30))

# same towns as scripts/fetch_chamoli_data.py (name, lat, lon)
TOWNS = [
    ("Gopeshwar", 30.408, 79.320), ("Chamoli", 30.402, 79.333),
    ("Joshimath", 30.555, 79.565), ("Badrinath", 30.743, 79.494),
    ("Govindghat", 30.620, 79.560), ("Pipalkoti", 30.429, 79.427),
    ("Nandprayag", 30.333, 79.317), ("Karnaprayag", 30.263, 79.217),
    ("Tharali", 30.075, 79.493), ("Gairsain", 30.050, 79.287),
]

# demo scenarios: (rain next 24 h, rain past 72 h) in mm per town
SCENARIOS = {
    "moderate": {"default": (20, 40), "joshimath": (40, 80), "nandprayag": (40, 80),
                 "pipalkoti": (40, 80)},
    "heavy": {"default": (45, 90), "joshimath": (90, 180), "nandprayag": (80, 170),
              "pipalkoti": (85, 160), "govindghat": (90, 170), "chamoli": (70, 150)},
}


def fetch_live():
    """One Open-Meteo call for all towns -> list of per-town dicts."""
    r = httpx.get(OPEN_METEO_FORECAST, timeout=30, headers={"User-Agent": USER_AGENT}, params={
        "latitude": ",".join(str(t[1]) for t in TOWNS),
        "longitude": ",".join(str(t[2]) for t in TOWNS),
        "hourly": "precipitation,snowfall,visibility",
        "current": "precipitation,weather_code",
        "past_days": 3, "forecast_days": 3, "timezone": "Asia/Kolkata"})
    r.raise_for_status()
    data = r.json()
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
            "rain_past_72h_mm": round(past72, 1), "rain_next_24h_mm": round(next24, 1),
            "snow_next_24h_cm": round(snow24, 1),
            "min_visibility_m": min(vis24) if vis24 else None,
            "weather_code_now": loc["current"].get("weather_code"),
            "rain_factor": rain_factor(next24, past72), "simulated": False,
        })
    return out


def apply_scenario(weather, scenario):
    """Replace rain values with a demo scenario (or return live data unchanged)."""
    if scenario not in SCENARIOS:
        return weather
    table = SCENARIOS[scenario]
    out = []
    for w in weather:
        nxt, past = table.get(w["point_id"], table["default"])
        out.append({**w, "rain_next_24h_mm": nxt, "rain_past_72h_mm": past,
                    "rain_factor": rain_factor(nxt, past), "simulated": True})
    return out


def alerts(weather):
    """Banner messages for towns where rain raises landslide risk."""
    out = []
    for w in weather:
        rf = w["rain_factor"]
        if rf >= 0.3:
            level = "severe" if rf >= 1.0 else "high" if rf >= 0.6 else "moderate"
            out.append({"town": w["name"], "level": level,
                        "message": f"{'Very heavy' if rf >= 1 else 'Heavy' if rf >= 0.6 else 'Moderate'}"
                                   f" rain near {w['name']}: {w['rain_next_24h_mm']} mm expected in "
                                   f"24 h ({w['rain_past_72h_mm']} mm in the last 72 h). "
                                   "Landslide risk is raised on nearby roads."})
        if (w.get("snow_next_24h_cm") or 0) >= 5:
            out.append({"town": w["name"], "level": "high",
                        "message": f"Snow expected near {w['name']} ({w['snow_next_24h_cm']} cm)."})
        if w.get("min_visibility_m") is not None and w["min_visibility_m"] < 200:
            out.append({"town": w["name"], "level": "moderate",
                        "message": f"Fog / low visibility near {w['name']}."})
    return out
