"""
SafeYatra API (FastAPI).

Run from the backend/ folder:
    ..\\.venv\\Scripts\\uvicorn app.main:app --reload
Interactive docs: http://127.0.0.1:8000/docs
"""

import asyncio
import gzip
import json
import uuid
from contextlib import asynccontextmanager
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config, weather as wx
from .auth import admin_user, current_user
from .data import AppData
from .risk import GSI_ALERT_FACTOR, RISK_WEIGHTS, NASA_SUSC_WEIGHT, update_live_risk
from .routing import (SAFETY_PRESETS, RoadGraph, compare, haversine, nearest_help, reasons)
from .store import REPORT_TYPES, Store

MAX_PHOTO_BYTES = 5 * 1024 * 1024
PHOTO_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
RAIN_SCENARIOS = ["live", "moderate", "heavy"]


# --------------------------------------------------------------------------- #
# App state: data + graph + database, and the live-risk refresh
# --------------------------------------------------------------------------- #

class State:
    def __init__(self):
        self.data = AppData()
        self.store = Store()
        self.live_weather = self.data.weather          # from the last pipeline run
        self.weather_updated_at = None
        self.refresh_risk()                            # fills risk_now before the graph uses it
        self.graph = RoadGraph(self.data.segments)
        self.seed_sample_closures()
        self.refresh_risk()

    @property
    def scenario(self):
        return self.store.get_setting("rain_scenario", "live")

    @property
    def gsi_alert(self):
        return self.store.get_setting("gsi_alert", "none")

    def weather_now(self):
        return wx.apply_scenario(self.live_weather, self.scenario)

    def refresh_risk(self):
        """Recompute risk_now for all roads from weather, GSI alert, closures, reports."""
        update_live_risk(self.data.segments, self.weather_now(), self.gsi_alert,
                         self.store.closed_segment_ids(), self.store.report_penalties())
        self.segments_json = None          # map layer is rebuilt on the next request

    def seed_sample_closures(self):
        """One example seasonal closure so the feature is visible in the demo."""
        if self.store.get_setting("seeded") or self.store.count_closures():
            return
        ids = self.graph.path_segment_ids((79.4940, 30.7430), (79.4960, 30.7710))
        if ids:
            year = date.today().year if date.today().month >= 5 else date.today().year - 1
            self.store.add_closure(
                name="Badrinath - Mana (winter snow)", reason="Seasonal snow closure (sample)",
                segment_ids=ids, start_date=f"{year}-11-15", end_date=f"{year + 1}-04-30",
                source="sample", created_by="system")
        self.store.set_setting("seeded", "1")


state: Optional[State] = None


async def weather_loop():
    """Refresh Open-Meteo weather every WEATHER_REFRESH_MIN minutes."""
    while True:
        try:
            state.live_weather = await asyncio.to_thread(wx.fetch_live)
            state.weather_updated_at = state.live_weather[0]["fetched_at"]
            state.refresh_risk()
        except Exception as err:       # keep the last good weather on any network error
            print(f"weather refresh failed: {err}")
        await asyncio.sleep(config.WEATHER_REFRESH_MIN * 60)


@asynccontextmanager
async def lifespan(app):
    global state
    state = State()
    task = asyncio.create_task(weather_loop())
    yield
    task.cancel()


app = FastAPI(title="SafeYatra API", version="0.1",
              description="Hazard-aware route planner for Chamoli district, Uttarakhand.",
              lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)
config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")


def parse_latlon(text, name):
    try:
        lat, lon = (float(x) for x in text.split(","))
    except ValueError:
        raise HTTPException(422, f"'{name}' must look like 30.408,79.320 (lat,lon)")
    return lat, lon


def feature(geom_type, coords, props):
    return {"type": "Feature", "geometry": {"type": geom_type, "coordinates": coords},
            "properties": props}


# --------------------------------------------------------------------------- #
# Public endpoints
# --------------------------------------------------------------------------- #

@app.get("/api/health")
def health():
    return {"status": "ok", "segments": len(state.data.segments),
            "auth_configured": bool(config.CLERK_JWKS_URL)}


@app.get("/api/places")
def places(q: str = "", limit: int = Query(10, le=50)):
    """Search Chamoli towns and villages by name (towns first)."""
    q = q.strip().lower()
    if not q:
        return [p for p in state.data.places if p["kind"] == "town"][:limit]
    starts = [p for p in state.data.places if p["name"].lower().startswith(q)]
    contains = [p for p in state.data.places
                if q in p["name"].lower() and not p["name"].lower().startswith(q)]
    return (starts + contains)[:limit]


@app.get("/api/places/nearest")
def nearest_place(lat: float, lon: float):
    """Name of the closest town or village (used to label map clicks)."""
    best = min(state.data.places, key=lambda p: haversine((p["lon"], p["lat"]), (lon, lat)))
    return {**best, "distance_m": round(haversine((best["lon"], best["lat"]), (lon, lat)))}


@app.get("/api/route")
def route(from_: str = Query(..., alias="from", description="lat,lon"),
          to: str = Query(..., description="lat,lon"),
          safety: float = Query(5, ge=0, le=20, description="0 fastest ... 10 safest")):
    """Safest route for the chosen safety level, plus the plain shortest route."""
    a, b = parse_latlon(from_, "from"), parse_latlon(to, "to")
    chosen = state.graph.route((a[1], a[0]), (b[1], b[0]), safety)
    if "error" in chosen:
        raise HTTPException(404, chosen["error"])
    shortest = chosen if safety == 0 else state.graph.route((a[1], a[0]), (b[1], b[0]), 0)

    towns = {state.data.by_id[i]["nearest_weather_point"] for i in chosen["segment_ids"]}
    weather_now = state.weather_now()
    alerts = [al for al in wx.alerts(weather_now) if al["town"].lower() in towns]
    return {
        "safe_route": chosen,
        "shortest_route": shortest,
        "comparison": compare(chosen, shortest),
        "weather_alerts": alerts,
        "gsi_alert": state.gsi_alert,
        "simulated_weather": state.scenario != "live",
        "nearest_help": nearest_help(chosen["geometry"]["coordinates"], state.data.pois),
    }


@app.get("/api/segments")
def segments(accept_encoding: str = Header(default="")):
    """All road segments, coloured by current risk (compact GeoJSON for the map).
    Built and gzipped once, cached until the risk changes (~2.8 MB, 0.5 MB gzipped)."""
    if state.segments_json is None:
        feats = [feature("LineString", [[round(x, 5), round(y, 5)] for x, y in s["coords"]], {
            "id": s["segment_id"], "highway": s["highway"], "name": s["name"], "ref": s["ref"],
            "risk": s["risk_now"], "cls": s["risk_class_now"], "closed": s["closed"]})
            for s in state.data.segments]
        raw = json.dumps({"type": "FeatureCollection", "features": feats},
                         separators=(",", ":")).encode()
        state.segments_json = (raw, gzip.compress(raw, compresslevel=6))
    raw, packed = state.segments_json
    if "gzip" in accept_encoding:
        return Response(packed, media_type="application/json",
                        headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding"})
    return Response(raw, media_type="application/json")


@app.get("/api/segments/{segment_id}")
def segment_detail(segment_id: str):
    """Everything about one road segment: risk, the factors behind it, nearby help."""
    s = state.data.by_id.get(segment_id)
    if not s:
        raise HTTPException(404, "Unknown segment")
    weights = dict(RISK_WEIGHTS)
    if s.get("susc_source") == "NASA":
        weights["susceptibility"] = NASA_SUSC_WEIGHT
    total = sum(weights[k] for k in s["risk_factors"])
    factors = [{"factor": k, "value": v, "weight": round(weights[k] / total, 3),
                "contribution": round(weights[k] * v / total, 3)}
               for k, v in s["risk_factors"].items()]
    detail = {k: v for k, v in s.items() if k not in ("coords", "risk_factors")}
    return {**detail, "factors": factors, "reasons": reasons(s),
            "geometry": {"type": "LineString", "coordinates": s["coords"]}}


@app.get("/api/landslides")
def landslides():
    return state.data.landslides


@app.get("/api/rivers")
def rivers(kind: Optional[str] = Query(None, description="river or stream")):
    if not kind:
        return state.data.rivers
    return {"type": "FeatureCollection",
            "features": [f for f in state.data.rivers["features"]
                         if f["properties"]["kind"] == kind]}


@app.get("/api/pois")
def pois(category: Optional[str] = None):
    if not category:
        return state.data.pois
    return {"type": "FeatureCollection",
            "features": [f for f in state.data.pois["features"]
                         if f["properties"]["category"] == category]}


@app.get("/api/boundary")
def boundary():
    return state.data.boundary


@app.get("/api/weather")
def weather():
    """Rain per town, banner alerts, GSI alert level, and whether a demo scenario is on."""
    w = state.weather_now()
    return {"towns": w, "alerts": wx.alerts(w), "scenario": state.scenario,
            "simulated": state.scenario != "live", "gsi_alert": state.gsi_alert,
            "updated_at": state.weather_updated_at or (w[0]["fetched_at"] if w else None)}


@app.get("/api/stats")
def stats():
    """Km of road per current risk class (home screen numbers)."""
    km = {c: 0.0 for c in ("low", "medium", "high", "very_high")}
    for s in state.data.segments:
        km[s["risk_class_now"]] += s["length_m"] / 1000
    closed_km = sum(s["length_m"] for s in state.data.segments if s["closed"]) / 1000
    return {"km_by_class": {k: round(v, 1) for k, v in km.items()},
            "total_km": round(sum(km.values()), 1), "closed_km": round(closed_km, 1),
            "landslides": len(state.data.landslides["features"]),
            "segments": len(state.data.segments)}


@app.get("/api/closures")
def closures():
    """Active road closures (public, so the map can show them)."""
    return [c for c in state.store.list_closures() if c["active"]]


# --------------------------------------------------------------------------- #
# Signed-in users: blockage reports
# --------------------------------------------------------------------------- #

@app.get("/api/me")
def me(user=Depends(current_user)):
    return user


@app.post("/api/reports")
async def create_report(type: str = Form(...), lat: float = Form(...), lon: float = Form(...),
                        description: str = Form(""), user_name: str = Form(""),
                        photo: Optional[UploadFile] = File(None), user=Depends(current_user)):
    """Report a landslide / blocked road. Adds temporary risk until an admin reviews it."""
    if type not in REPORT_TYPES:
        raise HTTPException(422, f"type must be one of {REPORT_TYPES}")
    node, dist = state.graph.nearest_node(lon, lat, main_only=False)
    if dist > 2000:
        raise HTTPException(422, "That point is more than 2 km from any road in Chamoli")
    # the segment touching the snapped node that passes closest to the point
    segs = {d["seg"]["segment_id"]: d["seg"] for _, _, d in state.graph.g.edges(node, data=True)}
    seg = min(segs.values(), key=lambda s: min(haversine(c, (lon, lat)) for c in s["coords"]))

    photo_name = None
    if photo and photo.filename:
        if photo.content_type not in PHOTO_TYPES:
            raise HTTPException(422, "Photo must be JPG, PNG or WebP")
        content = await photo.read()
        if len(content) > MAX_PHOTO_BYTES:
            raise HTTPException(422, "Photo must be under 5 MB")
        photo_name = uuid.uuid4().hex + PHOTO_TYPES[photo.content_type]
        (config.UPLOAD_DIR / photo_name).write_bytes(content)

    report = state.store.add_report(user_id=user["user_id"], user_name=user_name[:80] or None,
                                    type=type, description=description[:1000], lat=lat, lon=lon,
                                    segment_id=seg["segment_id"], photo=photo_name)
    state.refresh_risk()
    return report


@app.get("/api/reports/mine")
def my_reports(user=Depends(current_user)):
    return state.store.list_reports(user_id=user["user_id"])


@app.get("/api/reports/recent")
def recent_reports():
    """Pending + verified reports for the map (no user ids)."""
    out = []
    for r in state.store.list_reports():
        if r["status"] in ("pending", "verified"):
            out.append({k: r[k] for k in ("id", "type", "description", "lat", "lon", "status",
                                          "created_at", "photo")})
    return out[:200]


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #

class ReviewIn(BaseModel):
    status: str = Field(..., pattern="^(verified|rejected|pending)$")


class PointIn(BaseModel):
    lat: float
    lon: float


class ClosureIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    reason: str = ""
    start: PointIn
    end: PointIn
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class SettingsIn(BaseModel):
    gsi_alert: Optional[str] = None
    rain_scenario: Optional[str] = None


@app.get("/api/admin/reports")
def admin_reports(status: Optional[str] = None, user=Depends(admin_user)):
    return state.store.list_reports(status=status)


@app.patch("/api/admin/reports/{report_id}")
def review_report(report_id: int, body: ReviewIn, user=Depends(admin_user)):
    """Verify -> the road segment is closed for routing. Reject -> no effect."""
    report = state.store.get_report(report_id)
    if not report:
        raise HTTPException(404, "Unknown report")
    report = state.store.set_report_status(report_id, body.status, user["user_id"])
    linked = [c for c in state.store.list_closures() if c["report_id"] == report_id]
    if body.status == "verified" and not linked and report["segment_id"]:
        state.store.add_closure(name=f"Report #{report_id}: {report['type'].replace('_', ' ')}",
                                reason=report["description"], segment_ids=[report["segment_id"]],
                                source="report", report_id=report_id,
                                created_by=user["user_id"])
    elif body.status != "verified":
        for c in linked:
            state.store.delete_closure(c["id"])
    state.refresh_risk()
    return report


@app.get("/api/admin/closures")
def admin_closures(user=Depends(admin_user)):
    return state.store.list_closures()


@app.post("/api/admin/closures")
def add_closure(body: ClosureIn, user=Depends(admin_user)):
    """Close the road between two points (e.g. a seasonal snow closure)."""
    ids = state.graph.path_segment_ids((body.start.lon, body.start.lat),
                                       (body.end.lon, body.end.lat))
    if not ids:
        raise HTTPException(422, "Could not find a road between those two points")
    c = state.store.add_closure(name=body.name, reason=body.reason, segment_ids=ids,
                                start_date=body.start_date, end_date=body.end_date,
                                created_by=user["user_id"])
    state.refresh_risk()
    return c


@app.delete("/api/admin/closures/{closure_id}")
def delete_closure(closure_id: int, user=Depends(admin_user)):
    state.store.delete_closure(closure_id)
    state.refresh_risk()
    return {"deleted": closure_id}


@app.get("/api/admin/settings")
def get_settings(user=Depends(admin_user)):
    return {"gsi_alert": state.gsi_alert, "rain_scenario": state.scenario,
            "gsi_alert_options": list(GSI_ALERT_FACTOR), "rain_scenario_options": RAIN_SCENARIOS}


@app.put("/api/admin/settings")
def put_settings(body: SettingsIn, user=Depends(admin_user)):
    if body.gsi_alert is not None:
        if body.gsi_alert not in GSI_ALERT_FACTOR:
            raise HTTPException(422, f"gsi_alert must be one of {list(GSI_ALERT_FACTOR)}")
        state.store.set_setting("gsi_alert", body.gsi_alert)
    if body.rain_scenario is not None:
        if body.rain_scenario not in RAIN_SCENARIOS:
            raise HTTPException(422, f"rain_scenario must be one of {RAIN_SCENARIOS}")
        state.store.set_setting("rain_scenario", body.rain_scenario)
    state.refresh_risk()
    return get_settings(user)


@app.get("/api/safety-presets")
def safety_presets():
    return SAFETY_PRESETS
