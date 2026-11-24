"""Routing tests from the validation plan (section 24)."""

import random

import networkx as nx
import pytest

from app.data import AppData
from app.risk import update_live_risk
from app.routing import RoadGraph, haversine

TOWNS = {"Gopeshwar": (79.320, 30.408), "Joshimath": (79.565, 30.555),
         "Karnaprayag": (79.217, 30.263), "Badrinath": (79.494, 30.743),
         "Chamoli": (79.333, 30.402), "Tharali": (79.493, 30.075)}


@pytest.fixture(scope="module")
def graph():
    data = AppData()
    update_live_risk(data.segments, [])        # dry weather, no closures
    return RoadGraph(data.segments)


def test_lambda_zero_is_plain_shortest_path(graph):
    s, _ = graph.nearest_node(*TOWNS["Karnaprayag"])
    t, _ = graph.nearest_node(*TOWNS["Gopeshwar"])
    ours = sum(seg["length_m"] for seg, _ in graph.astar(s, t, 0))
    nx_len = nx.shortest_path_length(
        graph.g, s, t, weight=lambda u, v, e: min(d["seg"]["length_m"] for d in e.values()))
    assert ours == pytest.approx(nx_len, rel=1e-6)


@pytest.mark.parametrize("a,b", [("Karnaprayag", "Gopeshwar"), ("Chamoli", "Tharali"),
                                 ("Karnaprayag", "Badrinath")])
def test_more_safety_never_more_risk(graph, a, b):
    risks = [graph.route(TOWNS[a], TOWNS[b], lam)["route_risk_avg"] for lam in (0, 2, 5, 10)]
    assert all(r2 <= r1 + 1e-9 for r1, r2 in zip(risks, risks[1:]))


def test_single_road_route(graph):
    r = graph.route(TOWNS["Gopeshwar"], TOWNS["Joshimath"], 5)
    assert 50 < r["distance_km"] < 70           # ~59 km, only one road


def test_closed_roads_are_avoided(graph):
    r = graph.route(TOWNS["Karnaprayag"], TOWNS["Gopeshwar"], 0)
    blocked = r["segment_ids"][len(r["segment_ids"]) // 2]
    seg = next(d["seg"] for _, _, d in graph.g.edges(data=True)
               if d["seg"]["segment_id"] == blocked)
    seg["closed"] = True
    try:
        r2 = graph.route(TOWNS["Karnaprayag"], TOWNS["Gopeshwar"], 0)
        assert "error" in r2 or blocked not in r2["segment_ids"]
    finally:
        seg["closed"] = False


def test_heuristic_is_admissible(graph):
    """Straight-line distance never exceeds the real route cost."""
    rng = random.Random(1)
    nodes = list(graph.snap["main"][0])
    for _ in range(15):
        a, b = rng.sample(nodes, 2)
        a, b = a.item(), b.item()
        steps = graph.astar(a, b, 5)
        if steps:
            cost = sum(seg["length_m"] * (1 + 5 * seg["risk_now"]) for seg, _ in steps)
            assert haversine(graph.pos[a], graph.pos[b]) <= cost


def test_hazard_stretches_have_reasons(graph):
    r = graph.route(TOWNS["Karnaprayag"], TOWNS["Badrinath"], 0)
    for h in r["hazard_stretches"]:
        assert h["reasons"] and h["start_km"] <= h["end_km"] <= r["distance_km"] + 0.1
