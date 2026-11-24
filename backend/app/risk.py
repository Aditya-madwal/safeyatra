"""
Live ("dynamic") risk: the stored static_risk adjusted for current conditions.

    risk_now = landslide_part * (1 + rain_factor + gsi_alert_factor)
             + other_part     * (1 + fog_factor)
             + report_penalty                      (unverified blockage reports)
    capped at 1.0

landslide_part = the share of static_risk that comes from landslide factors
(susceptibility, past landslides, terrain slope); other_part = road bends.
Closed roads (verified blockages, seasonal closures) get closed = True and are
skipped by the router.
"""

from .routing import risk_class

# same weights as scripts/fetch_chamoli_data.py (RISK_WEIGHTS, NASA_SUSC_WEIGHT)
RISK_WEIGHTS = {"susceptibility": 0.30, "landslide_density": 0.20, "terrain_slope": 0.20,
                "curvature": 0.15, "accident_density": 0.15}
NASA_SUSC_WEIGHT = 0.10
LANDSLIDE_FACTORS = {"susceptibility", "landslide_density", "terrain_slope"}

GSI_ALERT_FACTOR = {"none": 0.0, "low": 0.3, "moderate": 0.6, "high": 1.0}
FOG_VISIBILITY_M = 200        # visibility below this -> fog factor
FOG_FACTOR = 0.2
REPORT_PENALTY = 0.3          # unverified report: temporary extra risk


def rain_factor(next24, past72):
    """Section 13 table: more rain -> higher landslide risk."""
    if next24 > 65 or past72 > 150:
        return 1.0
    if next24 >= 35 or past72 >= 75:
        return 0.6
    if next24 >= 10 or past72 >= 30:
        return 0.3
    return 0.0


def split_static_risk(seg):
    """(landslide_part, other_part) of a segment's static_risk."""
    factors = seg.get("risk_factors") or {}
    weights = dict(RISK_WEIGHTS)
    if seg.get("susc_source") == "NASA":
        weights["susceptibility"] = NASA_SUSC_WEIGHT
    total = sum(weights[k] for k in factors) or 1
    ls = sum(weights[k] * v for k, v in factors.items() if k in LANDSLIDE_FACTORS) / total
    other = sum(weights[k] * v for k, v in factors.items() if k not in LANDSLIDE_FACTORS) / total
    return ls, other


def update_live_risk(segments, weather, gsi_alert="none", closed_ids=(), penalties=None):
    """Recompute risk_now / risk_class_now / closed for every segment, in place."""
    by_point = {w["point_id"]: w for w in weather}
    g = GSI_ALERT_FACTOR.get(gsi_alert, 0.0)
    closed_ids, penalties = set(closed_ids), penalties or {}
    for s in segments:
        w = by_point.get(s.get("nearest_weather_point"))
        rf = w["rain_factor"] if w else 0.0
        vis = w.get("min_visibility_m") if w else None
        fog = FOG_FACTOR if vis is not None and vis < FOG_VISIBILITY_M else 0.0
        ls, other = split_static_risk(s)
        penalty = penalties.get(s["segment_id"], 0.0)
        r = min(ls * (1 + rf + g) + other * (1 + fog) + penalty, 1.0)
        s["rain_factor"] = rf
        s["report_penalty"] = penalty
        s["risk_now"] = round(r, 3)
        s["risk_class_now"] = risk_class(r)
        s["dynamic"] = round(r / s["static_risk"], 3) if s["static_risk"] else 1.0
        s["closed"] = s["segment_id"] in closed_ids
