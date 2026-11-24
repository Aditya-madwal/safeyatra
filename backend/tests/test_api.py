"""API tests (sign-in is faked in conftest.py; the database is temporary)."""

GOPESHWAR, JOSHIMATH = "30.408,79.320", "30.555,79.565"
KARNAPRAYAG = "30.263,79.217"


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_places_search(client):
    names = [p["name"] for p in client.get("/api/places?q=josh").json()]
    assert "Joshimath" in names


def test_route(client):
    r = client.get(f"/api/route?from={GOPESHWAR}&to={JOSHIMATH}&safety=5")
    assert r.status_code == 200
    body = r.json()
    assert body["safe_route"]["geometry"]["type"] == "LineString"
    assert 50 < body["safe_route"]["distance_km"] < 70
    assert "comparison" in body and "nearest_help" in body


def test_bad_coordinates(client):
    assert client.get("/api/route?from=abc&to=1,2").status_code == 422


def test_segments_and_detail(client):
    feats = client.get("/api/segments").json()["features"]
    assert len(feats) > 5000
    detail = client.get(f"/api/segments/{feats[0]['properties']['id']}").json()
    assert detail["factors"] and detail["reasons"]


def test_heavy_rain_scenario_raises_risk(client):
    before = client.get("/api/stats").json()["km_by_class"]
    client.put("/api/admin/settings", json={"rain_scenario": "heavy"})
    after = client.get("/api/stats").json()["km_by_class"]
    client.put("/api/admin/settings", json={"rain_scenario": "live"})
    assert after["high"] + after["very_high"] > before["high"] + before["very_high"]
    assert client.get("/api/weather").json()["simulated"] is False


def test_report_verify_closes_road(client):
    rep = client.post("/api/reports", data={"type": "landslide", "lat": 30.4798,
                                            "lon": 79.4679, "description": "Pagal Nala debris"})
    assert rep.status_code == 200
    rep = rep.json()
    assert rep["status"] == "pending" and rep["segment_id"]

    client.patch(f"/api/admin/reports/{rep['id']}", json={"status": "verified"})
    closed = {i for c in client.get("/api/closures").json() for i in c["segment_ids"]}
    assert rep["segment_id"] in closed

    client.patch(f"/api/admin/reports/{rep['id']}", json={"status": "rejected"})
    closed = {i for c in client.get("/api/closures").json() for i in c["segment_ids"]}
    assert rep["segment_id"] not in closed


def test_admin_closure_between_points(client):
    c = client.post("/api/admin/closures", json={
        "name": "Test closure", "start": {"lat": 30.3333, "lon": 79.3170},
        "end": {"lat": 30.3500, "lon": 79.3350}}).json()
    assert c["segment_ids"] and c["active"]
    client.delete(f"/api/admin/closures/{c['id']}")
