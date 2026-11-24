"""
Risk-aware routing with A* (NetworkX).

    edge cost  = length_m * (1 + lambda * risk_now)     (closed road -> not usable)
    heuristic  = straight-line (haversine) distance to the goal

cost >= length >= straight-line distance, so the heuristic never over-estimates
and A* returns the cheapest path for the chosen lambda (admissible heuristic).

lambda (the "safety slider"): 0 = shortest, 2 = balanced, 5 = safe, 10 = safest.
"""

import math

import networkx as nx
import numpy as np

EARTH_RADIUS_M = 6371008.8
SAFETY_PRESETS = {"fastest": 0, "balanced": 2, "safe": 5, "safest": 10}
# typical hill-road speeds (km/h) when OSM has no maxspeed
SPEED_KMH = {"trunk": 35, "primary": 30, "secondary": 25, "tertiary": 20}
DEFAULT_SPEED_KMH = 15
MAIN_ROADS = {"motorway", "trunk", "primary", "secondary", "tertiary"}
HIGH_CLASSES = ("high", "very_high")


def haversine(p1, p2):
    """Distance in metres between two (lon, lat) points."""
    lon1, lat1, lon2, lat2 = map(math.radians, (p1[0], p1[1], p2[0], p2[1]))
    a = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def base_class(highway):
    return (highway or "").replace("_link", "")


def risk_class(r):
    return "low" if r < 0.25 else "medium" if r < 0.5 else "high" if r < 0.75 else "very_high"


def travel_minutes(seg):
    return seg["length_m"] / 1000 / SPEED_KMH.get(base_class(seg["highway"]), DEFAULT_SPEED_KMH) * 60


def reasons(seg):
    """Plain-language reasons why a segment is risky (shown in the app)."""
    out = []
    if seg.get("landslides_within_500m"):
        out.append("landslide zone")
    if (seg.get("cross_slope_deg") or 0) >= 35:
        out.append("steep slope")
    if (seg.get("sharp_turns") or 0) >= 3 or (seg.get("curvature_deg_per_km") or 0) >= 1200:
        out.append("sharp bends")
    if seg.get("dist_to_river_m") is not None and seg["dist_to_river_m"] < 100:
        out.append("river erosion")
    if seg.get("stream_crossings"):
        out.append("nala crossing")
    if seg.get("rain_factor"):
        out.append("heavy rain")
    if seg.get("report_penalty"):
        out.append("reported blockage (unverified)")
    return out or ["steep terrain"]


class RoadGraph:
    def __init__(self, segments):
        self.g = nx.MultiDiGraph()
        self.pos = {}
        for s in segments:
            u, v = s["u_node"], s["v_node"]
            self.pos[u], self.pos[v] = s["coords"][0], s["coords"][-1]
            oneway = str(s.get("oneway") or "").lower()
            if oneway != "-1":
                self.g.add_edge(u, v, key=s["segment_id"], seg=s, rev=False)
            if oneway not in ("yes", "true", "1"):
                self.g.add_edge(v, u, key=s["segment_id"], seg=s, rev=True)

        # Start/end points snap to main-road nodes of the biggest connected
        # network, so a search never starts on a tiny cut-off bit of road.
        biggest = max(nx.weakly_connected_components(self.g), key=len)
        snap = [n for n in biggest
                if any(base_class(d["seg"]["highway"]) in MAIN_ROADS
                       for _, _, d in self.g.edges(n, data=True))]
        self.snap = {"main": (np.array(snap), np.array([self.pos[n] for n in snap]))}
        every = list(biggest)
        self.snap["all"] = (np.array(every), np.array([self.pos[n] for n in every]))

    def nearest_node(self, lon, lat, main_only=True):
        """Closest road node (flat-earth distance is fine inside one district)."""
        nodes, xy = self.snap["main" if main_only else "all"]
        dx = (xy[:, 0] - lon) * math.cos(math.radians(lat))
        dy = xy[:, 1] - lat
        i = int(np.argmin(dx * dx + dy * dy))
        node = nodes[i].item()
        return node, haversine(self.pos[node], (lon, lat))

    @staticmethod
    def _edge_cost(d, lam, ignore_closed=False):
        s = d["seg"]
        if s.get("closed") and not ignore_closed:
            return None
        return s["length_m"] * (1 + lam * s["risk_now"])

    def _best_edge(self, u, v, lam, ignore_closed=False):
        """Cheapest usable edge between u and v (there can be parallel roads)."""
        best = None
        for d in self.g[u][v].values():
            c = self._edge_cost(d, lam, ignore_closed)
            if c is not None and (best is None or c < best[0]):
                best = (c, d)
        return best

    def path_segment_ids(self, a_lonlat, b_lonlat):
        """Segment ids of the shortest road between two points (used to define closures)."""
        s, _ = self.nearest_node(*a_lonlat, main_only=False)
        t, _ = self.nearest_node(*b_lonlat, main_only=False)
        steps = self.astar(s, t, 0, ignore_closed=True) if s != t else None
        return [seg["segment_id"] for seg, _ in steps] if steps else []

    def astar(self, start, goal, lam, ignore_closed=False):
        """List of (segment, reversed) along the best path, or None if unreachable."""
        def weight(u, v, edges):
            best = self._best_edge(u, v, lam, ignore_closed)
            return None if best is None else best[0]     # None hides the edge

        def h(a, b):
            return haversine(self.pos[a], self.pos[b])

        try:
            nodes = nx.astar_path(self.g, start, goal, heuristic=h, weight=weight)
        except nx.NetworkXNoPath:
            return None
        steps = []
        for u, v in zip(nodes, nodes[1:]):
            d = self._best_edge(u, v, lam, ignore_closed)[1]
            steps.append((d["seg"], d["rev"]))
        return steps

    def route(self, start_lonlat, end_lonlat, lam):
        s, s_dist = self.nearest_node(*start_lonlat)
        t, t_dist = self.nearest_node(*end_lonlat)
        if s == t:
            return {"error": "Start and destination are at the same place on the road network."}
        steps = self.astar(s, t, lam)
        if steps is None:
            return {"error": "No open road connects these places (a road may be closed)."}
        out = summarize(steps)
        out["safety"] = lam
        out["snap_distance_m"] = {"start": round(s_dist), "end": round(t_dist)}
        return out


def summarize(steps):
    """Turn a path into what the app shows: line, km, time, risk, hazards, profile."""
    coords, km, profile, segs = [], 0.0, [], []
    for seg, rev in steps:
        c = seg["coords"][::-1] if rev else seg["coords"]
        coords += c if not coords else c[1:]
        elev = seg["elev_end_m"] if rev else seg["elev_start_m"]
        profile.append({"km": round(km, 2), "elev_m": elev, "risk": seg["risk_now"]})
        km += seg["length_m"] / 1000
        segs.append(seg)
    last, rev = steps[-1]
    profile.append({"km": round(km, 2), "elev_m": last["elev_start_m"] if rev else last["elev_end_m"],
                    "risk": last["risk_now"]})

    total_m = sum(s["length_m"] for s in segs)
    avg = sum(s["length_m"] * s["risk_now"] for s in segs) / total_m
    high_km = sum(s["length_m"] for s in segs if s["risk_class_now"] in HIGH_CLASSES) / 1000
    return {
        "geometry": {"type": "LineString", "coordinates": coords},
        "distance_km": round(total_m / 1000, 2),
        "est_time_min": round(sum(travel_minutes(s) for s in segs)),
        "route_risk_avg": round(avg, 3),
        "route_risk_max": round(max(s["risk_now"] for s in segs), 3),
        "risk_class": risk_class(avg),
        "high_risk_km": round(high_km, 2),
        "km_by_class": {c: round(sum(s["length_m"] for s in segs if s["risk_class_now"] == c)
                                 / 1000, 2) for c in ("low", "medium", "high", "very_high")},
        "hazard_stretches": hazard_stretches(segs),
        "segment_ids": [s["segment_id"] for s in segs],
        "profile": profile,
    }


def hazard_stretches(segs):
    """Group consecutive high / very-high segments into stretches with km markers."""
    out, km, cur = [], 0.0, None
    for s in segs:
        length = s["length_m"] / 1000
        if s["risk_class_now"] in HIGH_CLASSES:
            if cur and abs(cur["end_km"] - km) < 0.01:
                cur["end_km"] = km + length
                cur["reasons"] |= set(reasons(s))
                if s["risk_now"] > cur["max_risk"]:
                    cur["max_risk"], cur["worst_segment"] = s["risk_now"], s["segment_id"]
                cur["coords"] += s["coords"]
            else:
                cur = {"start_km": km, "end_km": km + length, "reasons": set(reasons(s)),
                       "max_risk": s["risk_now"], "worst_segment": s["segment_id"],
                       "coords": list(s["coords"])}
                out.append(cur)
        km += length
    for c in out:
        c["start_km"], c["end_km"] = round(c["start_km"], 1), round(c["end_km"], 1)
        c["reasons"] = sorted(c["reasons"])
        c["risk_class"] = risk_class(c["max_risk"])
        pts = c.pop("coords")
        c["location"] = pts[len(pts) // 2]      # [lon, lat] in the middle of the stretch
    return out


def nearest_help(route_coords, pois, max_dist_m=1500):
    """Hospitals, clinics, police and fuel within ~1.5 km of the route."""
    line = np.array(route_coords)
    # distance along the route at every vertex (km)
    steps = [0.0] + [haversine(a, b) / 1000 for a, b in zip(route_coords, route_coords[1:])]
    along = np.cumsum(steps)
    lat0 = math.radians(float(line[:, 1].mean()))
    out = []
    for ft in pois["features"]:
        p = ft["properties"]
        if p["category"] not in ("hospital", "clinic", "police", "fuel"):
            continue
        lon, lat = ft["geometry"]["coordinates"]
        dx = (line[:, 0] - lon) * math.cos(lat0) * 111_320
        dy = (line[:, 1] - lat) * 110_540
        d2 = dx * dx + dy * dy
        i = int(np.argmin(d2))
        dist = math.sqrt(float(d2[i]))
        if dist <= max_dist_m:
            out.append({"name": p.get("name") or p["category"].title(), "category": p["category"],
                        "phone": p.get("phone"), "lon": lon, "lat": lat,
                        "dist_from_route_m": round(dist), "at_km": round(float(along[i]), 1)})
    return sorted(out, key=lambda x: x["at_km"])


def compare(chosen, shortest):
    """How the chosen (safer) route compares with the plain shortest route."""
    def pct(a, b):
        return round((b - a) / b * 100) if b else 0
    return {
        "extra_km": round(chosen["distance_km"] - shortest["distance_km"], 2),
        "extra_min": chosen["est_time_min"] - shortest["est_time_min"],
        "risk_reduction_pct": pct(chosen["route_risk_avg"], shortest["route_risk_avg"]),
        "high_risk_km_reduction_pct": pct(chosen["high_risk_km"], shortest["high_risk_km"]),
        "same_route": chosen["segment_ids"] == shortest["segment_ids"],
    }
