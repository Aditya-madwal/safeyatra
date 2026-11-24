#!/usr/bin/env python3
"""
Generate UI mockup images of the planned SafeYatra app.

The maps use our REAL data from output/ (roads coloured by computed risk,
landslides, rivers, hospitals) and REAL routes found with a small A* search,
so the pictures show what the finished app would actually display.

Each screen is written as an HTML page and screenshotted with headless Chrome.

Usage:
    python scripts/make_mockups.py
Output:
    "app images for future reference/*.png"
"""

import heapq
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_chamoli_data as f   # reuse haversine, TOWNS, etc.

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
IMG_DIR = ROOT / "app images for future reference"
CHROME = "google-chrome"

RISK_COLORS = {"low": "#2e9d5b", "medium": "#e0b000", "high": "#ee7a10", "very_high": "#d62828"}
RISK_LABEL = {"low": "Low", "medium": "Medium", "high": "High", "very_high": "Very high"}
ROAD_WIDTH = {"trunk": 3.2, "primary": 2.8, "secondary": 2.4, "tertiary": 2.0}
MAIN = {"trunk", "primary", "secondary", "tertiary"}


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


SEGS = load("roads_segments.geojson")["features"]
BOUNDARY = load("boundary.geojson")["features"][0]["geometry"]
LANDSLIDES = load("landslides.geojson")["features"]
RIVERS = load("rivers.geojson")["features"]
POIS = load("pois.geojson")["features"]
TOWNS = {t[0]: (t[2], t[1]) for t in f.TOWNS}   # name -> (lon, lat)


# --------------------------------------------------------------------------- #
# Routing (A*) on the segment graph - same idea the real backend will use
# --------------------------------------------------------------------------- #

ADJ, POS = {}, {}
for ft in SEGS:
    p, c = ft["properties"], ft["geometry"]["coordinates"]
    POS[p["u_node"]], POS[p["v_node"]] = c[0], c[-1]
    ADJ.setdefault(p["u_node"], []).append((p["v_node"], ft, False))
    ADJ.setdefault(p["v_node"], []).append((p["u_node"], ft, True))
MAIN_NODES = {ft["properties"][k] for ft in SEGS
              if ft["properties"]["highway"].replace("_link", "") in MAIN
              for k in ("u_node", "v_node")}


def nearest_node(lonlat):
    return min(MAIN_NODES, key=lambda n: f.haversine(POS[n], lonlat))


def astar(a, b, lam):
    """cost = length * (1 + lambda * risk); heuristic = straight-line distance."""
    s, t = nearest_node(TOWNS[a]), nearest_node(TOWNS[b])
    h = lambda n: f.haversine(POS[n], POS[t])
    pq, g, prev = [(h(s), 0.0, s)], {s: 0.0}, {}
    while pq:
        _, gc, n = heapq.heappop(pq)
        if n == t:
            break
        if gc > g[n]:
            continue
        for m, ft, rev in ADJ[n]:
            p = ft["properties"]
            c = gc + p["length_m"] * (1 + lam * p["static_risk"])
            if c < g.get(m, 1e18):
                g[m], prev[m] = c, (n, ft, rev)
                heapq.heappush(pq, (c + h(m), c, m))
    steps, n = [], t
    while n != s:
        n, ft, rev = prev[n]
        steps.append((ft, rev))
    steps.reverse()
    coords, segs = [], []
    for ft, rev in steps:
        c = ft["geometry"]["coordinates"][::-1] if rev else ft["geometry"]["coordinates"]
        coords += c if not coords else c[1:]
        segs.append(ft["properties"])
    km = sum(p["length_m"] for p in segs) / 1000
    risk = sum(p["length_m"] * p["static_risk"] for p in segs) / (km * 1000)
    high_km = sum(p["length_m"] for p in segs if p["risk_class"] in ("high", "very_high")) / 1000
    minutes = sum(p["length_m"] / 1000 / {"trunk": 35, "primary": 30, "secondary": 25,
                                          "tertiary": 20}.get(p["highway"], 15) * 60 for p in segs)
    return {"coords": coords, "segs": segs, "km": km, "risk": risk, "high_km": high_km,
            "minutes": minutes}


def overall_class(r):
    return "low" if r < 0.25 else "medium" if r < 0.5 else "high" if r < 0.75 else "very_high"


def reasons(p):
    out = []
    if p["landslides_within_500m"]:
        out.append("landslide zone")
    if (p.get("cross_slope_deg") or 0) >= 35:
        out.append("steep slope")
    if p["sharp_turns"] >= 3 or p["curvature_deg_per_km"] >= 1200:
        out.append("sharp bends")
    if p.get("dist_to_river_m") is not None and p["dist_to_river_m"] < 100:
        out.append("river erosion")
    if p.get("stream_crossings"):
        out.append("nala crossing")
    return out or ["steep terrain"]


def hazard_stretches(route, min_class=("high", "very_high")):
    """Group consecutive high-risk segments into stretches with km markers."""
    out, km, cur = [], 0.0, None
    for p in route["segs"]:
        L = p["length_m"] / 1000
        if p["risk_class"] in min_class:
            if cur and abs(cur["end"] - km) < 0.01:
                cur["end"] = km + L
                cur["reasons"] |= set(reasons(p))
                cur["max"] = max(cur["max"], p["static_risk"])
            else:
                cur = {"start": km, "end": km + L, "reasons": set(reasons(p)),
                       "max": p["static_risk"]}
                out.append(cur)
        km += L
    return out


def nearest_town_name(lonlat):
    return min(TOWNS, key=lambda t: f.haversine(TOWNS[t], lonlat))


# --------------------------------------------------------------------------- #
# SVG map renderer
# --------------------------------------------------------------------------- #

class MapView:
    def __init__(self, bounds, w, h, pad=20):
        lon0, lat0, lon1, lat1 = bounds
        self.kx = math.cos(math.radians((lat0 + lat1) / 2))
        sx = (w - 2 * pad) / ((lon1 - lon0) * self.kx)
        sy = (h - 2 * pad) / (lat1 - lat0)
        self.s = min(sx, sy)
        self.cx, self.cy = (lon0 + lon1) / 2, (lat0 + lat1) / 2
        self.w, self.h = w, h

    def xy(self, c):
        return (self.w / 2 + (c[0] - self.cx) * self.kx * self.s,
                self.h / 2 - (c[1] - self.cy) * self.s)

    def path(self, coords):
        pts = [self.xy(c) for c in coords]
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def bounds_of(coords, margin=0.08):
    lons, lats = [c[0] for c in coords], [c[1] for c in coords]
    dx, dy = max(lons) - min(lons), max(lats) - min(lats)
    m = max(dx, dy) * margin + 0.01
    return (min(lons) - m, min(lats) - m, max(lons) + m, max(lats) + m)


def render_map(view, *, roads="risk", risk_key="risk_class", landslides=False,
               landslide_split=False, rivers=True, streams=False, pois=None,
               routes=(), markers=(), towns=True, highlight=None, dim_roads=False):
    v = view
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{v.w}" height="{v.h}" '
             f'viewBox="0 0 {v.w} {v.h}" style="display:block">',
             f'<rect width="{v.w}" height="{v.h}" fill="#e3e6df"/>']
    polys = [BOUNDARY["coordinates"]] if BOUNDARY["type"] == "Polygon" else BOUNDARY["coordinates"]
    for poly in polys:
        parts.append(f'<path d="{v.path(poly[0])} Z" fill="#f7f5ef" stroke="#8a8a8a" '
                     f'stroke-width="1.6" stroke-dasharray="7 4"/>')
    if rivers:
        for r in RIVERS:
            k = r["properties"]["kind"]
            if k == "stream" and not streams:
                continue
            parts.append(f'<path d="{v.path(r["geometry"]["coordinates"])}" fill="none" '
                         f'stroke="{"#9cc6e4" if k == "river" else "#c5dcec"}" '
                         f'stroke-width="{2.2 if k == "river" else 0.8}"/>')
    if roads:
        order = sorted(SEGS, key=lambda s: ROAD_WIDTH.get(
            s["properties"]["highway"].replace("_link", ""), 1.0))
        for s in order:
            p = s["properties"]
            cls = p[risk_key] if roads == "risk" else None
            col = RISK_COLORS[cls] if cls else "#9a9a9a"
            wdt = ROAD_WIDTH.get(p["highway"].replace("_link", ""), 1.1)
            op = 0.35 if dim_roads else 1
            parts.append(f'<path d="{v.path(s["geometry"]["coordinates"])}" fill="none" '
                         f'stroke="{col}" stroke-width="{wdt}" stroke-linecap="round" '
                         f'opacity="{op}"/>')
    for rt in routes:
        d = v.path(rt["coords"])
        if rt.get("style") == "alt":
            parts.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-width="8" '
                         f'stroke-linecap="round" stroke-linejoin="round"/>')
            parts.append(f'<path d="{d}" fill="none" stroke="#5b6270" stroke-width="4" '
                         f'stroke-dasharray="9 7" stroke-linecap="round"/>')
        else:
            parts.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-width="11" '
                         f'stroke-linecap="round" stroke-linejoin="round" opacity=".95"/>')
            parts.append(f'<path d="{d}" fill="none" stroke="#1d5fd1" stroke-width="6" '
                         f'stroke-linecap="round" stroke-linejoin="round"/>')
    if highlight:
        parts.append(f'<path d="{v.path(highlight)}" fill="none" stroke="#111" '
                     f'stroke-width="10" stroke-linecap="round" opacity=".25"/>')
    if landslides:
        for l in LANDSLIDES:
            x, y = v.xy(l["geometry"]["coordinates"])
            if not (0 <= x <= v.w and 0 <= y <= v.h):
                continue
            news = l["properties"]["source"] == "NEWS"
            fill = "#7b3fa0" if not (landslide_split and news) else "#c2185b"
            parts.append(f'<path d="M{x:.1f},{y - 6:.1f} L{x + 5.5:.1f},{y + 4:.1f} '
                         f'L{x - 5.5:.1f},{y + 4:.1f} Z" fill="{fill}" stroke="#fff" '
                         f'stroke-width="1.3"/>')
    if pois:
        icon = {"hospital": ("#d62828", "H"), "clinic": ("#e05a5a", "+"),
                "police": ("#1d4ed8", "P"), "fuel": ("#374151", "F")}
        for p in POIS:
            cat = p["properties"]["category"]
            if cat not in pois:
                continue
            x, y = v.xy(p["geometry"]["coordinates"])
            if not (0 <= x <= v.w and 0 <= y <= v.h):
                continue
            col, ch = icon[cat]
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{col}" stroke="#fff" '
                         f'stroke-width="1.6"/><text x="{x:.1f}" y="{y + 3.6:.1f}" '
                         f'font-size="10" font-weight="700" fill="#fff" '
                         f'text-anchor="middle">{ch}</text>')
    if towns:
        for name, c in TOWNS.items():
            x, y = v.xy(c)
            if not (10 <= x <= v.w - 10 and 10 <= y <= v.h - 10):
                continue
            dx, dy = {"Chamoli": (7, 15), "Gopeshwar": (-8, -8)}.get(name, (7, -6))
            anchor = "end" if dx < 0 else "start"
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="#222" '
                         f'stroke="#fff" stroke-width="1.5"/>'
                         f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}" '
                         f'class="lbl">{name}</text>')
    for m in markers:
        x, y = v.xy(m["at"])
        col = m.get("color", "#1d5fd1")
        parts.append(f'<g transform="translate({x:.1f},{y:.1f})">'
                     f'<path d="M0,0 C-9,-12 -12,-17 -12,-23 A12,12 0 1 1 12,-23 '
                     f'C12,-17 9,-12 0,0 Z" fill="{col}" stroke="#fff" stroke-width="2"/>'
                     f'<text x="0" y="-19" font-size="11" font-weight="700" fill="#fff" '
                     f'text-anchor="middle">{m.get("label", "")}</text></g>')
    parts.append("</svg>")
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# HTML building blocks
# --------------------------------------------------------------------------- #

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Inter","Ubuntu","DejaVu Sans",sans-serif;color:#1f2933;background:#fff;
     width:%(w)dpx;height:%(h)dpx;overflow:hidden;font-size:14px}
.top{height:56px;background:#14213d;color:#fff;display:flex;align-items:center;
     padding:0 22px;gap:14px}
.logo{font-weight:800;font-size:20px;letter-spacing:.2px}
.logo span{color:#f5b301}
.tag{font-size:12px;opacity:.75}
.nav{margin-left:auto;display:flex;gap:22px;font-size:13px;opacity:.9}
.nav b{border-bottom:2px solid #f5b301;padding-bottom:3px}
.main{display:flex;height:calc(100%% - 56px)}
.panel{width:380px;padding:18px;overflow:hidden;border-right:1px solid #e5e7eb;
       display:flex;flex-direction:column;gap:14px;background:#fbfbfa}
.mapwrap{position:relative;flex:1}
.lbl{font-size:12px;font-weight:600;fill:#1f2933;paint-order:stroke;stroke:#fff;
     stroke-width:3.5px;stroke-linejoin:round}
h2{font-size:17px}
h3{font-size:13px;text-transform:uppercase;letter-spacing:.6px;color:#6b7280}
.muted{color:#6b7280;font-size:12.5px}
.field{border:1px solid #d1d5db;border-radius:9px;padding:10px 12px;background:#fff;
       display:flex;align-items:center;gap:10px;font-size:14px}
.dot{width:10px;height:10px;border-radius:50%%;flex:none}
.btn{background:#1d5fd1;color:#fff;border-radius:9px;padding:11px;text-align:center;
     font-weight:700}
.btn.sec{background:#fff;color:#1d5fd1;border:1px solid #1d5fd1}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:14px}
.card.sel{border:2px solid #1d5fd1;box-shadow:0 2px 10px rgba(29,95,209,.15)}
.row{display:flex;align-items:center;gap:8px}
.badge{display:inline-block;padding:3px 9px;border-radius:999px;font-size:12px;
       font-weight:700;color:#fff}
.legend{position:absolute;right:16px;bottom:16px;background:#fff;border-radius:10px;
        padding:12px 14px;box-shadow:0 2px 12px rgba(0,0,0,.15);font-size:12.5px}
.legend div{display:flex;align-items:center;gap:8px;margin-top:5px}
.sw{width:22px;height:5px;border-radius:3px}
.float{position:absolute;background:#fff;border-radius:10px;
       box-shadow:0 2px 14px rgba(0,0,0,.18)}
.slider{position:relative;height:34px;margin-top:6px}
.track{position:absolute;top:13px;left:6px;right:6px;height:6px;border-radius:3px;
       background:linear-gradient(90deg,#9ca3af,#1d5fd1)}
.knob{position:absolute;top:5px;width:22px;height:22px;border-radius:50%%;background:#fff;
      border:3px solid #1d5fd1;box-shadow:0 1px 4px rgba(0,0,0,.3)}
.ticks{display:flex;justify-content:space-between;font-size:11.5px;color:#6b7280}
.stretch{border-left:4px solid;padding:8px 10px;background:#fff;border-radius:6px;
         font-size:13px;margin-bottom:7px}
.alert{background:#fff4e5;border:1px solid #f5b301;border-radius:10px;padding:11px 13px;
       font-size:13px}
.alert.red{background:#fdecec;border-color:#d62828}
.chip{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:999px;
      padding:2px 8px;font-size:11.5px;margin:2px 3px 0 0}
table{border-collapse:collapse;width:100%%;font-size:13px}
th{text-align:left;color:#6b7280;font-weight:600;padding:9px 10px;
   border-bottom:1px solid #e5e7eb;font-size:12px;text-transform:uppercase}
td{padding:10px;border-bottom:1px solid #f0f0f0}
.toggle{width:34px;height:19px;border-radius:999px;background:#d1d5db;position:relative;flex:none}
.toggle.on{background:#1d5fd1}
.toggle:after{content:"";position:absolute;top:2px;left:2px;width:15px;height:15px;
              border-radius:50%%;background:#fff}
.toggle.on:after{left:17px}
.caption{position:absolute;left:16px;top:16px;background:rgba(20,33,61,.88);color:#fff;
         padding:7px 12px;border-radius:8px;font-size:12.5px}
"""


def page(body, w=1440, h=900, active="Route"):
    nav = "".join(f"<b>{n}</b>" if n == active else f"<span>{n}</span>"
                  for n in ("Route", "Risk map", "Weather", "Report", "Admin"))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<style>{CSS % {"w": w, "h": h}}</style></head><body>
<div class="top"><div class="logo">Safe<span>Yatra</span></div>
<div class="tag">Hazard-aware routes for Chamoli</div><div class="nav">{nav}</div></div>
<div class="main">{body}</div></body></html>"""


def legend(extra=""):
    rows = "".join(f'<div><span class="sw" style="background:{RISK_COLORS[k]}"></span>'
                   f'{RISK_LABEL[k]} risk</div>' for k in RISK_COLORS)
    return f'<div class="legend"><b>Road risk</b>{rows}{extra}</div>'


def risk_badge(cls, text=None):
    return (f'<span class="badge" style="background:{RISK_COLORS[cls]}">'
            f'{text or RISK_LABEL[cls] + " risk"}</span>')


def fmt_time(minutes):
    return f"{int(minutes // 60)} h {int(minutes % 60):02d} min"


def screenshot(html, name, w=1440, h=900):
    IMG_DIR.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                     encoding="utf-8") as tmp:
        tmp.write(html)
    out = IMG_DIR / name
    # headless Chrome loses some height to (invisible) browser UI, so render
    # taller and crop back to the exact size with Pillow
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", f"--window-size={w},{h + 200}",
                    f"--screenshot={out}", f"file://{tmp.name}"],
                   check=True, capture_output=True)
    Path(tmp.name).unlink()
    from PIL import Image
    Image.open(out).crop((0, 0, w, h)).save(out)
    print("saved", out.relative_to(ROOT))


def stats_by_class():
    km = {k: 0.0 for k in RISK_COLORS}
    for s in SEGS:
        km[s["properties"]["risk_class"]] += s["properties"]["length_m"] / 1000
    return km


# --------------------------------------------------------------------------- #
# Screens
# --------------------------------------------------------------------------- #

MAP_W, MAP_H = 1440 - 380, 900 - 56
DISTRICT = f.geometry_bbox(BOUNDARY)


def s01_home():
    v = MapView(DISTRICT, MAP_W, MAP_H)
    km = stats_by_class()
    total = sum(km.values())
    bars = "".join(f'<div style="flex:{km[k]:.0f};background:{RISK_COLORS[k]}"></div>'
                   for k in RISK_COLORS)
    rows = "".join(f'<div class="row" style="justify-content:space-between">'
                   f'<span class="row"><span class="dot" style="background:{RISK_COLORS[k]}">'
                   f'</span>{RISK_LABEL[k]}</span><b>{km[k]:,.0f} km</b></div>' for k in RISK_COLORS)
    panel = f"""<div class="panel">
<h2>Where are you going?</h2>
<div class="field"><span class="dot" style="background:#2e9d5b"></span>
  <span class="muted">Starting point</span></div>
<div class="field"><span class="dot" style="background:#d62828"></span>
  <span class="muted">Destination</span></div>
<div class="btn">Find safe route</div>
<div class="card"><h3>Chamoli road network today</h3>
 <div style="font-size:26px;font-weight:800;margin:6px 0">{total:,.0f} km</div>
 <div style="display:flex;height:10px;border-radius:5px;overflow:hidden;margin-bottom:10px">{bars}</div>
 <div style="display:flex;flex-direction:column;gap:6px">{rows}</div></div>
<div class="alert">&#9729; No heavy rain expected in the next 24 h. Landslide risk is at its
 normal level.</div>
<div class="muted">Risk combines past landslides, terrain slope, road bends and river
 erosion. Data: OpenStreetMap, NASA, news reports, Open-Meteo.</div>
</div>"""
    m = render_map(v, landslides=True)
    body = (panel + f'<div class="mapwrap">{m}<div class="caption">Risk map of Chamoli: every '
            f'road coloured by landslide and terrain risk</div>'
            + legend('<div><svg width="22" height="12"><path d="M11,1 L17,11 L5,11 Z" '
                     'fill="#7b3fa0"/></svg>Past landslide</div>') + '</div>')
    screenshot(page(body, active="Risk map"), "01_home_risk_map.png")


def s02_search():
    v = MapView(DISTRICT, MAP_W, MAP_H)
    opts = [("Gopeshwar", "District HQ · 1,550 m"), ("Gopeshwar – Chopta road", "Road"),
            ("Gopinath Temple, Gopeshwar", "Temple"), ("Gauchar", "Town · near Karnaprayag")]
    dd = "".join(f'<div style="padding:10px 12px;border-top:1px solid #f0f0f0;'
                 f'{"background:#eef4ff;" if i == 0 else ""}"><b>{a}</b>'
                 f'<div class="muted">{b}</div></div>' for i, (a, b) in enumerate(opts))
    panel = f"""<div class="panel">
<h2>Plan your trip</h2>
<div class="field" style="border-color:#1d5fd1;box-shadow:0 0 0 3px rgba(29,95,209,.15)">
 <span class="dot" style="background:#2e9d5b"></span><span>Gop<span style="border-left:2px solid
 #1d5fd1;margin-left:1px"></span></span></div>
<div class="card" style="padding:0;overflow:hidden;margin-top:-8px">{dd}</div>
<div class="field"><span class="dot" style="background:#d62828"></span>
  <span class="muted">Destination</span></div>
<div><h3>Popular routes</h3>
 <div style="display:flex;flex-direction:column;gap:7px;margin-top:8px">
 <div class="card" style="padding:10px 12px">Gopeshwar → Joshimath</div>
 <div class="card" style="padding:10px 12px">Karnaprayag → Badrinath</div>
 <div class="card" style="padding:10px 12px">Chamoli → Tharali</div></div></div>
<div class="muted">Tip: you can also click on the map to choose a point.</div>
</div>"""
    m = render_map(v, markers=[{"at": TOWNS["Gopeshwar"], "label": "A", "color": "#2e9d5b"}])
    body = panel + f'<div class="mapwrap">{m}{legend()}</div>'
    screenshot(page(body), "02_route_search.png")


def s03_compare(safe, short):
    allc = safe["coords"] + short["coords"]
    v = MapView(bounds_of(allc, 0.25), MAP_W, MAP_H)
    red = (1 - safe["high_km"] / short["high_km"]) * 100 if short["high_km"] else 0

    def card(r, title, sel, note):
        cls = overall_class(r["risk"])
        return f"""<div class="card {'sel' if sel else ''}">
 <div class="row" style="justify-content:space-between"><b>{title}</b>{risk_badge(cls)}</div>
 <div style="font-size:22px;font-weight:800;margin:6px 0">{r['km']:.1f} km
  <span class="muted" style="font-size:14px;font-weight:500">· {fmt_time(r['minutes'])}</span></div>
 <div class="muted">Risk score {r['risk']:.2f} · {r['high_km']:.1f} km of high-risk road</div>
 <div style="margin-top:6px;font-size:12.5px">{note}</div></div>"""
    panel = f"""<div class="panel">
<div class="field"><span class="dot" style="background:#2e9d5b"></span>Karnaprayag</div>
<div class="field"><span class="dot" style="background:#d62828"></span>Gopeshwar</div>
<div><h3>Safety preference</h3>
 <div class="slider"><div class="track"></div><div class="knob" style="left:calc(100% - 28px)"></div></div>
 <div class="ticks"><span>Fastest</span><span>Balanced</span><span>Safe</span><b style="color:#1d5fd1">Safest</b></div></div>
{card(safe, "&#128737; Safest route", True,
      f"Avoids the NH-7 slide stretch between Nandprayag and Chamoli · <b>{red:.0f}% less high-risk road</b>")}
{card(short, "&#9889; Shortest route", False,
      f"{safe['km'] - short['km']:.1f} km shorter but passes the Sonala and Chhinka slide zones")}
<div class="btn">Start with safest route</div>
</div>"""
    m = render_map(v, dim_roads=True, landslides=True,
                   routes=[{**short, "style": "alt"}, safe],
                   markers=[{"at": safe["coords"][0], "label": "A", "color": "#2e9d5b"},
                            {"at": safe["coords"][-1], "label": "B", "color": "#d62828"}])
    leg = ('<div class="legend"><b>Routes</b><div><span class="sw" style="background:#1d5fd1">'
           '</span>Safest (λ = 10)</div><div><span class="sw" style="background:repeating-linear-'
           'gradient(90deg,#5b6270 0 6px,transparent 6px 10px)"></span>Shortest (λ = 0)</div>'
           '<div><svg width="22" height="12"><path d="M11,1 L17,11 L5,11 Z" fill="#7b3fa0"/></svg>'
           'Past landslide</div></div>')
    body = panel + f'<div class="mapwrap">{m}{leg}</div>'
    screenshot(page(body), "03_route_comparison_safety_slider.png")


def risk_profile_svg(route, w=344, h=110):
    total = route["km"]
    x, bars, pts = 0.0, [], []
    elevs = [p.get("elev_start_m") for p in route["segs"] if p.get("elev_start_m") is not None]
    e0, e1 = min(elevs), max(elevs)
    for p in route["segs"]:
        L = p["length_m"] / 1000
        bw = L / total * w
        bars.append(f'<rect x="{x / total * w:.1f}" y="{h - 14}" width="{bw + .3:.1f}" '
                    f'height="10" fill="{RISK_COLORS[p["risk_class"]]}"/>')
        if p.get("elev_start_m") is not None:
            pts.append(f"{x / total * w:.1f},{(h - 22) - (p['elev_start_m'] - e0) / (e1 - e0) * (h - 34):.1f}")
        x += L
    return (f'<svg width="{w}" height="{h + 14}"><polyline points="{" ".join(pts)}" fill="none" '
            f'stroke="#4b5563" stroke-width="1.6"/>{"".join(bars)}'
            f'<text x="0" y="10" font-size="10" fill="#6b7280">{e1:,.0f} m</text>'
            f'<text x="0" y="{h - 24}" font-size="10" fill="#6b7280">{e0:,.0f} m</text>'
            f'<text x="0" y="{h + 10}" font-size="10" fill="#6b7280">0 km</text>'
            f'<text x="{w}" y="{h + 10}" font-size="10" fill="#6b7280" text-anchor="end">'
            f'{total:.0f} km</text></svg>')


def s04_breakdown(route):
    st = hazard_stretches(route)
    v = MapView(bounds_of(route["coords"], 0.12), MAP_W, MAP_H)
    km, places = 0.0, []
    for p in route["segs"]:
        km += p["length_m"] / 1000
    items = ""
    acc = 0.0
    seg_mid = []
    for p in route["segs"]:
        seg_mid.append((acc + p["length_m"] / 2000, p))
        acc += p["length_m"] / 1000
    for s in st[:5]:
        mid_km = (s["start"] + s["end"]) / 2
        # find coordinates near mid_km for a place name
        run, where = 0.0, route["coords"][0]
        for i in range(len(route["coords"]) - 1):
            run += f.haversine(route["coords"][i], route["coords"][i + 1]) / 1000
            if run >= mid_km:
                where = route["coords"][i]
                break
        cls = overall_class(s["max"])
        chips = "".join(f'<span class="chip">{r}</span>' for r in sorted(s["reasons"]))
        items += (f'<div class="stretch" style="border-color:{RISK_COLORS[cls]}">'
                  f'<div class="row" style="justify-content:space-between"><b>km {s["start"]:.1f} – '
                  f'{s["end"]:.1f}</b>{risk_badge(cls)}</div><div class="muted">near '
                  f'{nearest_town_name(where)}</div><div>{chips}</div></div>')
    cls = overall_class(route["risk"])
    panel = f"""<div class="panel" style="gap:11px">
<div class="row" style="justify-content:space-between"><h2>Gopeshwar → Joshimath</h2>{risk_badge(cls)}</div>
<div class="row" style="gap:18px"><div><div style="font-size:21px;font-weight:800">{route['km']:.1f} km</div>
 <div class="muted">distance</div></div><div><div style="font-size:21px;font-weight:800">
 {fmt_time(route['minutes'])}</div><div class="muted">est. time</div></div><div>
 <div style="font-size:21px;font-weight:800">{route['risk']:.2f}</div><div class="muted">risk score</div></div></div>
<div class="alert" style="font-size:12.5px">&#9888; <b>Only one road connects these towns.</b>
 The safest and shortest routes are the same, so drive carefully on the stretches below.</div>
<div><h3>Risk and elevation along the route</h3>{risk_profile_svg(route)}</div>
<div><h3 style="margin-bottom:7px">Dangerous stretches ({len(st)})</h3>{items}</div>
</div>"""
    m = render_map(v, dim_roads=True, landslides=True, routes=[route],
                   markers=[{"at": route["coords"][0], "label": "A", "color": "#2e9d5b"},
                            {"at": route["coords"][-1], "label": "B", "color": "#d62828"}])
    body = panel + f'<div class="mapwrap">{m}{legend()}</div>'
    screenshot(page(body), "04_route_risk_breakdown.png")


def s05_layers():
    b = (79.36, 30.38, 79.60, 30.60)    # Pipalkoti - Joshimath valley
    v = MapView(b, MAP_W, MAP_H)
    m = render_map(v, landslides=True, landslide_split=True, streams=True,
                   pois={"hospital", "clinic"})
    layers = [("Road risk colours", True), ("Past landslides (NASA)", True),
              ("Past landslides (news 2021–25)", True), ("Rivers and streams", True),
              ("Hospitals and clinics", True), ("Slope heat-map", False),
              ("District boundary", True), ("Weather (rain forecast)", False)]
    rows = "".join(f'<div class="row" style="justify-content:space-between;padding:7px 0;'
                   f'border-bottom:1px solid #f2f2f2"><span>{n}</span><span class="toggle '
                   f'{"on" if on else ""}"></span></div>' for n, on in layers)
    panel = f"""<div class="panel">
<h2>Map layers</h2>
<div class="muted">Turn hazard layers on and off to see why a road is risky.</div>
<div class="card" style="padding:6px 14px">{rows}</div>
<div class="card"><h3>In this view</h3>
 <div class="row" style="margin-top:8px"><svg width="16" height="14"><path d="M8,1 L15,13 L1,13 Z"
  fill="#7b3fa0"/></svg> NASA catalogue landslide (2007–17)</div>
 <div class="row" style="margin-top:6px"><svg width="16" height="14"><path d="M8,1 L15,13 L1,13 Z"
  fill="#c2185b"/></svg> Reported in news (2021–25)</div>
 <div class="row" style="margin-top:6px"><span class="sw" style="background:#9cc6e4"></span>
  Alaknanda river and nalas</div></div>
<div class="muted">Clusters of landslides along the Alaknanda valley (Pagal Nala,
 Patalganga, Helang) line up with the red stretches of NH-7.</div>
</div>"""
    body = (panel + f'<div class="mapwrap">{m}<div class="caption">Pipalkoti – Joshimath '
            f'section of NH-7 (Alaknanda valley)</div>{legend()}</div>')
    screenshot(page(body, active="Risk map"), "05_hazard_layers.png")


def s06_segment_popup():
    seg = max(SEGS, key=lambda s: s["properties"]["static_risk"]
              if f.is_nh7(s["properties"]) else -1)
    p = seg["properties"]
    mid = seg["geometry"]["coordinates"][len(seg["geometry"]["coordinates"]) // 2]
    b = (mid[0] - 0.06, mid[1] - 0.045, mid[0] + 0.06, mid[1] + 0.045)
    v = MapView(b, MAP_W, MAP_H)
    m = render_map(v, landslides=True, streams=True, highlight=seg["geometry"]["coordinates"])
    x, y = v.xy(mid)
    fac = p["risk_factors"]
    names = {"landslide_density": "Past landslides nearby", "terrain_slope": "Terrain slope",
             "curvature": "Road bends", "susceptibility": "GSI susceptibility",
             "accident_density": "Accidents"}
    bars = "".join(f'<div style="margin-top:8px"><div class="row" style="justify-content:'
                   f'space-between;font-size:12.5px"><span>{names[k]}</span><b>{val:.2f}</b></div>'
                   f'<div style="height:7px;background:#eee;border-radius:4px"><div style="height:7px;'
                   f'width:{val * 100:.0f}%;background:{RISK_COLORS[overall_class(val)]};'
                   f'border-radius:4px"></div></div></div>' for k, val in fac.items())
    cls = p["risk_class"]
    pop = f"""<div class="float" style="left:{x - 400:.0f}px;top:{max(20, y - 260):.0f}px;width:340px;padding:16px">
<div class="row" style="justify-content:space-between"><b style="font-size:15px">NH-7 near
 Nandprayag</b>{risk_badge(cls)}</div>
<div class="muted" style="margin-top:3px">Segment {p['segment_id']} · {p['length_m']:.0f} m ·
 trunk road</div>
<div style="font-size:30px;font-weight:800;margin:8px 0 2px">{p['static_risk']:.2f}
 <span class="muted" style="font-size:13px;font-weight:500">risk score (0 – 1)</span></div>
<h3 style="margin-top:8px">Why is it risky?</h3>{bars}
<div style="margin-top:12px;display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:12.5px">
 <div>&#9650; {p['landslides_within_500m']} landslides nearby</div>
 <div>&#8736; Slope {p['cross_slope_deg']:.0f}°</div>
 <div>&#8776; River {p['dist_to_river_m']:.0f} m away</div>
 <div>&#9873; Elevation {p['elev_start_m']:.0f} m</div></div>
<div class="alert red" style="margin-top:12px;font-size:12.5px">Blocked 5 times in news reports
 (2024 – 2025). Avoid during heavy rain.</div></div>"""
    panel = """<div class="panel"><h2>Road details</h2>
<div class="muted">Click any road on the map to see its risk score and the factors behind it.</div>
<div class="card"><h3>How the score is made</h3><div style="font-size:13px;margin-top:8px;line-height:1.6">
risk = weighted sum of<br>&nbsp;• past landslides nearby<br>&nbsp;• terrain slope<br>&nbsp;• road bends
<br>&nbsp;• landslide susceptibility (GSI, coming soon)<br><span class="muted">Each factor is
scaled 0 – 1 before weighting.</span></div></div>
<div class="card"><h3>Risk classes</h3><div style="font-size:13px;margin-top:8px;line-height:1.8">
<span class="badge" style="background:#2e9d5b">Low</span> &lt; 0.25<br>
<span class="badge" style="background:#e0b000">Medium</span> 0.25 – 0.50<br>
<span class="badge" style="background:#ee7a10">High</span> 0.50 – 0.75<br>
<span class="badge" style="background:#d62828">Very high</span> ≥ 0.75</div></div></div>"""
    body = panel + f'<div class="mapwrap">{m}{pop}{legend()}</div>'
    screenshot(page(body, active="Risk map"), "06_road_segment_details.png")


def s07_weather():
    # Example monsoon scenario: apply the dynamic multiplier from section 10.5
    scenario = {"Joshimath": (58, 96), "Pipalkoti": (72, 140), "Chamoli": (61, 118),
                "Gopeshwar": (55, 104), "Nandprayag": (49, 92), "Karnaprayag": (38, 70),
                "Govindghat": (66, 121), "Badrinath": (40, 85), "Tharali": (22, 48),
                "Gairsain": (18, 40)}
    rf = {t: f.rain_factor(a, b) for t, (a, b) in scenario.items()}
    for s in SEGS:
        p = s["properties"]
        c = s["geometry"]["coordinates"]
        town = nearest_town_name(c[len(c) // 2])
        # simplified dynamic multiplier for the picture: risk_now = static * (1 + 0.6 * rain_factor)
        now = min(1.0, p["static_risk"] * (1 + 0.6 * rf[town]))
        p["risk_now_demo"] = overall_class(now)
    v = MapView(DISTRICT, MAP_W, MAP_H)
    m = render_map(v, risk_key="risk_now_demo")
    rows = "".join(
        f'<tr><td><b>{t}</b></td><td>{a} mm</td><td>{b} mm</td><td>'
        f'{risk_badge("very_high" if rf[t] >= 1 else "high" if rf[t] >= .6 else "medium" if rf[t] >= .3 else "low", f"+{rf[t]:.1f}")}'
        f'</td></tr>' for t, (a, b) in sorted(scenario.items(), key=lambda kv: -rf[kv[0]]))
    panel = f"""<div class="panel" style="gap:11px">
<div class="alert red"><b>&#9928; Heavy rain warning – next 24 h</b><br>Very heavy rain expected
 in the Alaknanda valley after 2 PM. Landslide risk on NH-7 between Chamoli and Joshimath is
 <b>raised</b>. Avoid travel after dark.</div>
<div class="alert" style="font-size:12.5px"><b>GSI landslide forecast:</b> Moderate (orange)
 alert for Chamoli district today.</div>
<div class="card" style="padding:6px 4px"><table><tr><th>Town</th><th>Next 24 h</th>
 <th>Past 72 h</th><th>Extra risk</th></tr>{rows}</table></div>
<div class="muted">Example monsoon day. Rain data from Open-Meteo is refreshed every hour; the
 extra risk is added to the landslide part of each road's score.</div></div>"""
    body = (panel + f'<div class="mapwrap">{m}<div class="caption">Example: risk map on a heavy-'
            f'rain monsoon day – more roads turn orange and red</div>{legend()}</div>')
    screenshot(page(body, active="Weather"), "07_weather_alerts.png")


def s08_help(route):
    v = MapView(bounds_of(route["coords"], 0.10), MAP_W, MAP_H)
    m = render_map(v, dim_roads=True, routes=[route], pois={"hospital", "clinic", "police", "fuel"},
                   markers=[{"at": route["coords"][0], "label": "A", "color": "#2e9d5b"},
                            {"at": route["coords"][-1], "label": "B", "color": "#d62828"}])
    # POIs within 1.5 km of the route, with km marker along route
    cum, acc = [0.0], 0.0
    for i in range(len(route["coords"]) - 1):
        acc += f.haversine(route["coords"][i], route["coords"][i + 1]) / 1000
        cum.append(acc)
    found = []
    for p in POIS:
        cat = p["properties"]["category"]
        if cat not in ("hospital", "clinic", "police", "fuel"):
            continue
        if "physio" in (p["properties"]["name"] or "").lower():
            continue
        c = p["geometry"]["coordinates"]
        i = min(range(0, len(route["coords"]), 3), key=lambda k: f.haversine(route["coords"][k], c))
        d = f.haversine(route["coords"][i], c)
        if d < 1500:
            found.append((cum[i], cat, p["properties"]["name"] or cat.title(), d))
    found.sort()
    icon = {"hospital": ("#d62828", "H"), "clinic": ("#e05a5a", "+"), "police": ("#1d4ed8", "P"),
            "fuel": ("#374151", "F")}
    seen, items = set(), ""
    for km, cat, name, d in found:
        key = (cat, round(km))
        if key in seen:
            continue
        seen.add(key)
        col, ch = icon[cat]
        items += (f'<div class="row" style="padding:8px 0;border-bottom:1px solid #f2f2f2">'
                  f'<span style="width:24px;height:24px;border-radius:50%;background:{col};color:#fff;'
                  f'display:flex;align-items:center;justify-content:center;font-weight:700;'
                  f'font-size:12px;flex:none">{ch}</span><div style="flex:1"><b>{name}</b><div '
                  f'class="muted">{cat.title()} · {d:.0f} m off route</div></div><b>km {km:.0f}</b></div>')
        if len(seen) >= 9:
            break
    panel = f"""<div class="panel" style="gap:11px">
<h2>Help along your route</h2><div class="muted">Gopeshwar → Joshimath · within 1.5 km of the road</div>
<div class="row" style="gap:6px"><span class="chip" style="background:#fdecec;color:#b91c1c">Hospitals</span>
 <span class="chip" style="background:#fdecec;color:#b91c1c">Clinics</span>
 <span class="chip">Police</span><span class="chip" style="background:#f3f4f6;color:#374151">Fuel</span></div>
<div class="card" style="padding:4px 14px">{items}</div>
<div class="alert red" style="font-size:13px"><b>Emergency numbers</b><br>Ambulance 108 · Police 112 ·
 SDRF Uttarakhand 1070</div></div>"""
    body = panel + f'<div class="mapwrap">{m}</div>'
    screenshot(page(body), "08_nearest_help.png")


def s09_report():
    b = (79.36, 30.40, 79.56, 30.50)
    v = MapView(b, 1440, MAP_H)
    m = render_map(v, landslides=True,
                   markers=[{"at": (79.4679, 30.4798), "label": "!", "color": "#d62828"}])
    form = """<div class="float" style="left:50%;top:50%;transform:translate(-50%,-50%);width:440px;padding:22px">
<div class="row" style="justify-content:space-between"><h2>&#9888; Report a road problem</h2>
 <span class="muted" style="font-size:20px">×</span></div>
<div class="muted" style="margin:4px 0 14px">Location: NH-7 near Pagal Nala (30.480 N, 79.468 E)</div>
<h3>What happened?</h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0 14px">
 <div class="card" style="border:2px solid #d62828;text-align:center;padding:10px"><b>Landslide /<br>debris</b></div>
 <div class="card" style="text-align:center;padding:10px">Road<br>closed</div>
 <div class="card" style="text-align:center;padding:10px">Accident</div>
 <div class="card" style="text-align:center;padding:10px">Other</div></div>
<h3>Details (optional)</h3>
<div class="field" style="margin:8px 0 14px;height:64px;align-items:flex-start;color:#374151">
 Debris on both lanes, JCB not yet here. Cars waiting on Pipalkoti side.</div>
<div class="row" style="gap:10px;margin-bottom:16px"><div class="card" style="width:84px;height:62px;
 display:flex;align-items:center;justify-content:center;background:#f3f4f6">&#128247;</div>
 <span class="muted">Add a photo – it helps admins verify quickly</span></div>
<div class="btn" style="background:#d62828">Submit report</div>
<div class="muted" style="margin-top:10px;text-align:center">Reports are checked by an admin. Verified
 blockages are removed from routing.</div></div>"""
    body = (f'<div class="mapwrap" style="width:100%">{m}<div style="position:absolute;inset:0;'
            f'background:rgba(15,23,42,.35)"></div>{form}</div>')
    screenshot(page(body, active="Report"), "09_report_blockage.png")


def s10_admin():
    reports = [("R-1042", "Landslide / debris", "NH-7, Pagal Nala", "12 min ago", "pending", "1 photo"),
               ("R-1041", "Road closed", "Joshimath – Malari road, Tamak", "48 min ago", "pending", "—"),
               ("R-1039", "Landslide / debris", "NH-7, Nandprayag", "2 h ago", "verified", "2 photos"),
               ("R-1037", "Other", "Gopeshwar – Chopta road", "5 h ago", "rejected", "—"),
               ("R-1033", "Landslide / debris", "NH-7, Bhanerpani", "9 h ago", "expired", "1 photo")]
    col = {"pending": "#e0b000", "verified": "#2e9d5b", "rejected": "#6b7280", "expired": "#9ca3af"}
    rows = "".join(f'<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td>{d}</td><td>{f_}</td>'
                   f'<td><span class="badge" style="background:{col[e]}">{e}</span></td><td>'
                   + ('<span class="btn" style="padding:5px 10px;font-size:12px">Verify</span> '
                      '<span class="btn sec" style="padding:5px 10px;font-size:12px">Reject</span>'
                      if e == "pending" else '<span class="muted">—</span>') + '</td></tr>'
                   for a, b, c, d, e, f_ in reports)
    closures = [("Badrinath – Mana", "Snow closure", "15 Nov – 30 Apr", "yearly"),
                ("Joshimath – Malari (Tamak bridge)", "Bridge washed away", "31 Aug – until repaired", "once"),
                ("Gopeshwar – Chopta", "Snow closure", "1 Jan – 31 Mar", "yearly")]
    crow = "".join(f'<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td>{d}</td></tr>'
                   for a, b, c, d in closures)
    v = MapView((79.38, 30.30, 79.62, 30.62), 430, 330, pad=8)
    m = render_map(v, dim_roads=True, towns=False,
                   markers=[{"at": (79.4679, 30.4798), "label": "!", "color": "#e0b000"},
                            {"at": (79.3199, 30.3316), "label": "✓", "color": "#2e9d5b"},
                            {"at": (79.4283, 30.4334), "label": "×", "color": "#9ca3af"}])
    stat = lambda n, l, c: (f'<div class="card" style="flex:1"><div class="muted">{l}</div>'
                            f'<div style="font-size:26px;font-weight:800;color:{c}">{n}</div></div>')
    body = f"""<div style="padding:22px 26px;width:100%;display:flex;flex-direction:column;gap:16px">
<div class="row" style="justify-content:space-between"><h2 style="font-size:21px">Admin dashboard</h2>
 <span class="muted">Signed in as admin · Chamoli control room</span></div>
<div class="row" style="gap:14px">{stat(2, "Pending reports", "#b58900")}{stat(1, "Verified today", "#2e9d5b")}
{stat(3, "Active closures", "#d62828")}{stat("+0.6", "Current rain factor (Pipalkoti)", "#ee7a10")}</div>
<div class="row" style="gap:16px;align-items:flex-start">
<div class="card" style="flex:1;padding:6px 6px"><div style="padding:8px 10px"><b>User reports</b></div>
 <table><tr><th>ID</th><th>Type</th><th>Location</th><th>When</th><th>Photo</th><th>Status</th><th>Action</th></tr>{rows}</table></div>
<div class="card" style="width:460px;padding:14px"><b>Report locations</b><div style="margin-top:10px;
 border-radius:8px;overflow:hidden">{m}</div></div></div>
<div class="card" style="padding:6px"><div class="row" style="justify-content:space-between;padding:8px 10px">
 <b>Road closures</b><span class="btn" style="padding:6px 12px;font-size:12.5px">+ Add closure</span></div>
 <table><tr><th>Road</th><th>Reason</th><th>Dates</th><th>Repeats</th></tr>{crow}</table></div>
</div>"""
    screenshot(page(body, active="Admin"), "10_admin_panel.png")


def s11_mobile(route):
    W, H = 390, 844
    v = MapView(bounds_of(route["coords"], 0.12), W, 470, pad=10)
    m = render_map(v, dim_roads=True, routes=[route], towns=True,
                   markers=[{"at": route["coords"][0], "label": "A", "color": "#2e9d5b"},
                            {"at": route["coords"][-1], "label": "B", "color": "#d62828"}])
    st = hazard_stretches(route)
    cls = overall_class(route["risk"])
    items = "".join(f'<div class="stretch" style="border-color:{RISK_COLORS[overall_class(s["max"])]};'
                    f'padding:6px 9px;font-size:12.5px"><b>km {s["start"]:.1f}–{s["end"]:.1f}</b> · '
                    f'{", ".join(sorted(s["reasons"])[:2])}</div>' for s in st[:3])
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS % {"w": W, "h": H}}
.sheet{{position:absolute;left:0;right:0;bottom:0;height:410px;background:#fff;border-radius:18px 18px 0 0;
 box-shadow:0 -4px 18px rgba(0,0,0,.18);padding:10px 16px 16px;display:flex;flex-direction:column;gap:10px}}
</style></head><body style="position:relative">
<div style="height:28px;background:#14213d;color:#fff;font-size:12px;display:flex;align-items:center;
 justify-content:space-between;padding:0 14px"><b>9:41</b><span>&#9679;&#9679;&#9679; 4G</span></div>
<div style="position:absolute;top:38px;left:12px;right:12px;z-index:2" class="field">
 <b class="logo" style="font-size:15px;color:#14213d">Safe<span>Yatra</span></b>
 <span class="muted">Gopeshwar → Joshimath</span></div>
<div style="position:absolute;top:28px">{m}</div>
<div class="sheet"><div style="width:40px;height:5px;border-radius:3px;background:#d1d5db;margin:0 auto"></div>
<div class="row" style="justify-content:space-between"><div><div style="font-size:22px;font-weight:800">
 {fmt_time(route['minutes'])}</div><div class="muted">{route['km']:.1f} km · safest = shortest</div></div>
 {risk_badge(cls)}</div>
<div class="alert" style="font-size:12.5px;padding:8px 10px">&#9928; Rain after 2 PM – start early</div>
<div><h3 style="margin-bottom:6px">Watch out</h3>{items}</div>
<div class="row" style="gap:8px;margin-top:auto"><div class="btn" style="flex:1">Start</div>
 <div class="btn sec" style="flex:1">Download offline</div></div></div>
</body></html>"""
    screenshot(html, "11_mobile_view.png", W, H)


def main():
    print("computing routes with A* ...")
    safe = astar("Karnaprayag", "Gopeshwar", 10)
    short = astar("Karnaprayag", "Gopeshwar", 0)
    gj = astar("Gopeshwar", "Joshimath", 5)
    s01_home()
    s02_search()
    s03_compare(safe, short)
    s04_breakdown(gj)
    s05_layers()
    s06_segment_popup()
    s07_weather()
    s08_help(gj)
    s09_report()
    s10_admin()
    s11_mobile(gj)


if __name__ == "__main__":
    main()
