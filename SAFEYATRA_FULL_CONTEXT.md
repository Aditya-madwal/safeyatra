# SafeYatra: Complete Project Context and Status

> **One file with everything about this project:** what it is, why it exists, the tech stack, data sources and APIs, every decision made so far, progress, what each file and folder does, and the plan ahead.
>
> **Last updated:** 24 Nov 2026
> **Project folder:** `/home/aditya/gisproject`
> **Study area:** Chamoli district, Uttarakhand, India
> **Type:** Final-year college project (GIS + web app)
>
> The original hand-off spec is `project_context.md`; it was written before any work started. **This file supersedes it** wherever the two differ, because it records what was actually built and decided.

---

## 0. Start here (for a new agent picking up this project)

**Read in this order:** §0 (this) → §4 (decisions; must follow) → §10 (files) → §18 (data have/lack) → **§32 (next steps; your work queue)** → §33 (gotchas). Everything else is reference.

### Who the user is and how to work with them
- A **final-year college student** (GIS Developer role on a team project). Comfortable running commands when given them, but **not deeply technical**. They asked for explanations "in simple terms" and "start to end, clear to understand".
- When the user must do something by hand (websites, QGIS, forms), give **numbered step-by-step instructions** with the exact menu names and buttons. Use tables for summaries. Short sentences, no jargon (or explain it).
- **Keep everything at college level** (D1): simple, readable Python with comments; no heavy infrastructure. Prefer a few clear scripts over clever abstractions.
- The user likes being told **what's done, what's left, and what they need to do**, as short lists.
- They are happy for the agent to **do things itself** (e.g., they asked the agent to install QGIS and to research landslides on the web) rather than hand them back.
- **Do not** put the user's email or name into any external request (User-Agent etc.); use `CONTACT_EMAIL` from `.env` only if the user sets it (D5).
- **Do not** `git init` / commit / push unless the user asks. The folder is not a git repo yet.
- Recorded decisions (§4) are final. Don't reopen them (e.g., don't bring back the accident feature, D4).

### Update 24 Nov 2026 (evening): app built, project moved to Windows
- **Machine is now Windows 11**, project at `C:\Users\Aditya\Desktop\gisproject`, Python **3.12.3** venv in `.venv` (`.venv\Scripts\python.exe`), Node 22, QGIS **3.44.15 LTR** (installed via winget). Linux paths/commands below are historical.
- **NASA global landslide susceptibility map** (`data/raw/nasa_susceptibility/`, ~1 km, 5 classes → 1–4) replaces the missing GSI data, with a **lower weight (0.10 instead of 0.30)** because it rates almost all of Chamoli "very high". GSI files in `data/manual/` override it automatically. New segment field `susc_source`.
- New pipeline step `places` → `output/places.json` (1,068 towns/villages for search).
- Risk now: low 56 km · medium 1,891 · high 384 · very high 1.
- **Backend** (`backend/`, FastAPI + NetworkX A\* + SQLite) and **frontend** (`frontend/`, React + Vite + **DaisyUI 5** + Leaflet + **Clerk** `@clerk/react` v6) are built and working. 16 pytest tests pass. Run instructions: `README.md`.
- User decisions: **auth = Clerk**, **UI = DaisyUI**, **frontend = React (JS)**. API keys go in the single root `.env` (user fills them).

### Current state in one paragraph (before the app was built)
Phase 0 (setup) and phase 1 (data collection) are **done**. `scripts/fetch_chamoli_data.py` builds a 5,820-segment road network for Chamoli with elevation, slope proxy, bends, landslide exposure (NASA + 40 news events), river distance, stream crossings, nearest hospital, weather, and a preview risk score. Everything is in `output/`. QGIS is installed and the user has saved a project. Eleven app mockups exist in `app images for future reference/`. **Blocked:** GSI Bhukosh (susceptibility + inventory) is offline, and only the user can request it. **Next for the agent:** proper slope raster → GeoPandas pipeline / GeoPackage → A\* routing module → FastAPI backend → React frontend (§32).

---

## Table of contents

0. [Start here (for a new agent)](#0-start-here-for-a-new-agent-picking-up-this-project)

1. [What is SafeYatra?](#1-what-is-safeyatra)
2. [Problem and purpose](#2-problem-and-purpose)
3. [Scope and study area](#3-scope-and-study-area)
4. [Ground rules and decisions](#4-ground-rules-and-decisions)
5. [Team roles](#5-team-roles)
6. [Features](#6-features)
7. [Tech stack](#7-tech-stack)
8. [Development environment setup](#8-development-environment-setup)
9. [Data sources and APIs (with live status)](#9-data-sources-and-apis-with-live-status)
10. [Folder and file guide](#10-folder-and-file-guide)
11. [The data pipeline: `fetch_chamoli_data.py`](#11-the-data-pipeline-fetch_chamoli_datapy)
12. [Output files and their fields](#12-output-files-and-their-fields)
13. [Risk model](#13-risk-model)
14. [Current results (latest run)](#14-current-results-latest-run)
15. [Rivers report](#15-rivers-report)
16. [Landslide dataset from web research](#16-landslide-dataset-from-web-research)
17. [App mockups](#17-app-mockups)
18. [Data inventory: what we have and what we lack](#18-data-inventory-what-we-have-and-what-we-lack)
19. [App design: how it will work](#19-app-design-how-it-will-work)
20. [Routing (A*) design](#20-routing-a-design)
21. [Backend API design](#21-backend-api-design)
22. [Frontend design](#22-frontend-design)
23. [Implementation plan and phase status](#23-implementation-plan-and-phase-status)
24. [Validation and testing plan](#24-validation-and-testing-plan)
25. [Known limitations and caveats](#25-known-limitations-and-caveats)
26. [Licensing and attribution](#26-licensing-and-attribution)
27. [Open tasks (who does what)](#27-open-tasks-who-does-what)
28. [How-to: common commands](#28-how-to-common-commands)
29. [Progress log (what happened, in order)](#29-progress-log-what-happened-in-order)
30. [Reference links](#30-reference-links)
31. [Glossary](#31-glossary)
32. [NEXT STEPS: detailed hand-off plan](#32-next-steps-detailed-hand-off-plan)
33. [Gotchas and lessons learned](#33-gotchas-and-lessons-learned)

---

## 1. What is SafeYatra?

**SafeYatra** ("safe journey") is a **GIS-based route planner that is aware of hazards** on the mountain roads of Uttarakhand.

- Normal navigation apps find the **fastest** route.
- SafeYatra gives every road segment a **risk score** (mainly **landslide risk**, plus terrain danger such as steep slopes and sharp bends).
- It uses the **A\* (A-Star)** search algorithm to recommend routes that **balance distance against safety**, controlled by a **"Fastest ↔ Safest" slider**.
- It **warns travellers** about dangerous stretches, rain alerts and the nearest hospitals.

**Pitch line:** *Commercial maps tell you where a problem already is. SafeYatra tells you where problems are likely to happen.*

**Phase 1 focus:** **Chamoli district**. It has the highest landslide frequency in Uttarakhand and contains the **Rishikesh–Badrinath highway (NH-7)**, Char Dham pilgrim traffic, Joshimath, Gopeshwar, Karnaprayag and Govindghat.

---

## 2. Problem and purpose

### Problem
- Mountain roads in Uttarakhand suffer frequent **landslides** (especially in the monsoon, June–September), **sharp hairpin bends**, **steep drops** and high accident rates.
- Travellers (tourists, pilgrims, locals) have **no tool that shows where the risky stretches are** or **how risky a route is** before they set out.
- Google Maps and similar apps **react to incidents after they happen** and don't model terrain or landslide risk.

### Goals
1. Collect, clean and analyse geographic data for Chamoli: roads, terrain, landslides, rivers, weather and help points.
2. Compute a **risk score for every road segment**.
3. Provide **risk-aware routing** with A\*, using a user-controlled safety balance (λ).
4. Show **warnings and safety information**: risky stretches, rain alerts, nearest hospital.
5. Build a **user-friendly web platform** (mobile later).
6. Keep the design **extendable to other districts** (Rudraprayag, Uttarkashi, Tehri, Pithoragarh…).

### Key framing for the viva or presentation
In mountain districts there is often **only one road** between two towns, so the "safest" route often **equals** the shortest. The product is therefore presented as **"risk-aware routing + warnings"**, not just "alternative routes". Even on a single road it shows **which parts** are dangerous, warns about **rain today**, and lists the **nearest help**.
- Real example from our data: **Gopeshwar → Joshimath** has only one road (59.2 km).
- Real example where routes differ: **Karnaprayag → Gopeshwar**. The safest route is 41.5 km and the shortest 39.8 km, and the safe route has **27% less high-risk road**.

---

## 3. Scope and study area

| Item | Value |
|---|---|
| District | Chamoli, Uttarakhand, India |
| OSM relation id | **374815** (Overpass area id = 3600000000 + 374815 = **3600374815**) |
| Area (computed) | **7,832.7 km²** (brief said ~7,700) |
| Bounding box (computed, WGS84) | lon **79.076 – 80.102** E, lat **29.926 – 31.072** N |
| Analysis CRS (planned for QGIS/GeoPandas) | **EPSG:32644** (WGS 84 / UTM 44N, metres) |
| Storage / web CRS | **EPSG:4326** (lat/lon) for GeoJSON and APIs |
| Current script's metric calculations | Equirectangular local projection around lat 30.4° (accurate to well under 1% inside one district) |

### Key towns (approximate coordinates, used for weather sampling and checks)

| Town | Lat | Lon |
|---|---|---|
| Gopeshwar (district HQ) | 30.408 | 79.320 |
| Chamoli | 30.402 | 79.333 |
| Joshimath (Jyotirmath) | 30.555 | 79.565 |
| Badrinath | 30.743 | 79.494 |
| Govindghat | 30.620 | 79.560 |
| Pipalkoti | 30.429 | 79.427 |
| Nandprayag | 30.333 | 79.317 |
| Karnaprayag | 30.263 | 79.217 |
| Tharali | 30.075 | 79.493 |
| Gairsain | 30.050 | 79.287 |

### Key roads
- **NH-7** (Rishikesh–Badrinath). In OSM, `ref` = "NH7"; 177.3 km inside the district, continuous from Karnaprayag to Badrinath.
- Karnaprayag–Gwaldam–Tharali road (NH-109K)
- Gopeshwar–Ukhimath road (via Mandal and Chopta)
- Karnaprayag–Gairsain road
- Joshimath–Malari road (NH-107B)

### MVP demo routes
Gopeshwar → Joshimath · Karnaprayag → Badrinath · Chamoli → Tharali · Gopeshwar → Chopta direction · Karnaprayag → Gopeshwar (a pair where the routes differ)

---

## 4. Ground rules and decisions

These were decided during development and must be respected going forward.

| # | Decision | Reason |
|---|---|---|
| D1 | **Keep everything at final-year college level.** Simple, readable Python; no production-grade over-engineering (no Celery, Kubernetes, vector tiles or pgRouting unless asked). | User instruction: "this is a college project, we don't have to take things beyond college level" |
| D2 | **Python 3** in a project venv (`.venv`, Python **3.10.12**). | 3.10 is the newest Python on the machine; the spec allows 3.10+ |
| D3 | **Phase 1 script uses only `requests` + the standard library** (+ **Pillow** to read elevation tiles). GeoPandas etc. come in phase 2. | Easy to run anywhere; matches the spec |
| D4 | **Accident feature DROPPED.** No `accidents.csv` data collection. The accident weight (0.15) is shared out among the other factors automatically; road bends and sharp turns act as the road-danger stand-in. The loader code stays, and `data/manual/accidents.csv` exists with headers only. | User decision: "let's not do this accident feature" |
| D5 | **The user's email is NOT put in the HTTP User-Agent.** The script reads an optional `CONTACT_EMAIL` from `.env`; the default User-Agent is `SafeYatra/0.1 (student project)`. | Privacy; the user never approved sharing it |
| D6 | **Default elevation source is AWS Terrain Tiles** (free, no key, ~30 m), not Open-Meteo. | Open-Meteo's free elevation API counts every point as one call (600/min, ~10k/day) and blocked us after ~600 points; 23k points are needed |
| D7 | **NASA landslides fall back to the Global Landslide Catalog CSV** because the COOLR ArcGIS endpoints in the spec are dead (404 / DNS failure). | Verified on 24 Nov 2026 |
| D8 | **Landslide records with poor location accuracy (25 km, 50 km, unknown) are kept in the GeoJSON but NOT used for risk.** Only accuracy ≤ 10 km (exact, 1km, 5km, 10km, gsi_inventory, stream-crossing, village-level, approximate) counts. | They were pinned to town or district centres and created a false hotspot at Chamoli town |
| D9 | **Rivers are attributes only for now** (`dist_to_river_m`, `stream_crossings`), not in the risk formula. | The spec's formula doesn't include them; adding them later is a one-line change |
| D10 | **The backend loads data files into memory** (GeoJSON/GeoPackage → NetworkX graph); PostGIS is optional, added only if the guide wants a database. | College-level simplicity (D1) |
| D11 | **QGIS installed as the Flatpak "LTS" branch (3.28.9)**, user-level install. | No sudo needed. Note: the Flathub LTS branch is old (2023) and no longer updated; the "stable" branch is available if a newer version is wanted |
| D12 | **Google Maps is not a data source.** | Its APIs don't expose incidents; the terms forbid caching it or mixing it with our own routing; scraping breaks the terms |

---

## 5. Team roles

| Role | Responsibilities |
|---|---|
| **GIS Developer** | Collect, prepare, analyse and manage geographic data (boundary, roads, DEM/slope, landslides). Compute road-segment risk attributes. Export GeoPackage / GeoTIFF / CSV / GeoJSON for teammates. Tools: QGIS, Python. |
| **Backend / Routing** | Road graph, risk-weighted A\*, FastAPI service, live-data updaters (weather). |
| **Frontend** | Web map UI (React + Leaflet), route search, risk display, warnings, report-a-blockage. |
| **Data / Validation (shared)** | Validation of risk scores, report, documentation, presentation. |

### GIS Developer's 6-step workflow (from the brief)
1. **Collect geographic data**: boundary, roads, elevation, landslides (accidents dropped).
2. **Prepare data in QGIS**: clean, clip to Chamoli, check CRS, fix geometry.
3. **Create maps**: boundary, road network, elevation, slope, landslide maps.
4. **Spatial analysis**: roads near landslides, overlapping hazard zones.
5. **Road risk attributes**: per-segment length, slope, hazard exposure, etc.
6. **Export final GIS datasets**: clean GeoPackage, GeoTIFF and CSV files for teammates.

---

## 6. Features

### Core (MVP)
- **Risk map of Chamoli roads**: every segment colour-coded low / medium / high / very high.
- **Safe route search**: start + destination → **safest** and **shortest** routes side by side.
- **Safety slider (λ)**: Fastest · Balanced · Safe · Safest (λ = 0, 2, 5, 10).
- **Route risk breakdown**: distance, estimated time, route risk score, list of **dangerous stretches** with km markers and reasons ("landslide zone", "steep slope", "sharp bends", "river erosion", "nala crossing").
- **Hazard layer switches**: landslides (NASA / news / GSI), rivers and streams, hospitals, slope, boundary.
- **Road segment details on click**: risk score and the factors behind it.

### Phase 2 (live / dynamic)
- **Weather-aware risk**: next-24 h forecast and past-72 h rain raise landslide risk (Open-Meteo, hourly refresh).
- **GSI landslide forecast input**: when GSI issues a bulletin for Chamoli, raise risk in the affected areas (entered by hand).
- **Report a blockage**: users report landslides or closures with location + photo; an admin verifies; verified blockages remove the road from routing.
- **Admin panel**: verify or reject reports; manage closures (e.g., the winter snow closure beyond Joshimath/Badrinath).
- **Live incidents (optional)**: TomTom/HERE, if they have coverage in Chamoli.

### Phase 3 (nice to have)
- **Nearest help**: hospitals, clinics, police, fuel, SDRF along the route.
- **Travel-time advice**: "avoid after dark", "heavy rain expected after 2 PM".
- **Offline mode / downloadable route**.
- **Mobile app** (React Native / Flutter) or a responsive web layout.
- **Multi-district expansion**.
- **Multilingual UI** (Hindi / English / Garhwali).

### Dropped
- ~~Accident hotspots / accident risk component~~ (decision D4).

---

## 7. Tech stack

### Used so far

| Layer | Tool | Notes |
|---|---|---|
| Language | **Python 3.10.12** | venv at `.venv` |
| HTTP | **requests** 2.34 | All API calls, with caching and retries |
| Images | **Pillow** 12.3 | Reads the Terrarium PNG elevation tiles; crops the mockup screenshots |
| Desktop GIS | **QGIS 3.28.9 LTS** (Flatpak) | Viewing and checking data, making maps; project saved at `qgis/safeyatra.qgz` |
| Mockup rendering | **Google Chrome (headless)** + HTML/SVG | Used by `scripts/make_mockups.py` |
| Formats | GeoJSON, CSV, JSON | GeoPackage/GeoTIFF planned for phase 2 exports |

### Planned (phases 2–7), kept at college level

| Layer | Choice | Why |
|---|---|---|
| GIS processing (phase 2) | `geopandas`, `shapely` 2.x, `pyproj`, `rasterio`, `rasterstats`, `numpy`, `pandas` | Standard open-source geospatial stack (already listed, commented out, in `requirements.txt`) |
| Routing | **NetworkX** `astar_path` with a custom weight | Simple, in-memory, standard A\* |
| Backend | **FastAPI** + Uvicorn + Pydantic | Same language as the pipeline; auto docs at `/docs` |
| Scheduler | APScheduler (or a simple loop / cron) | Hourly weather refresh |
| Database | **None for MVP** (files loaded into memory). Optional: PostgreSQL + PostGIS | D10 |
| Frontend | **React + Vite**, **Leaflet** (react-leaflet), Tailwind CSS (optional) | Simple, free, OSM tiles |
| Base map tiles | OSM tiles (respect usage policy) or OpenTopoMap | Free |
| Place search | Local list of Chamoli places (+ Nominatim fallback) | Free, low volume |
| Mobile (later) | Responsive web, or React Native / Flutter | |
| Version control | Git + GitHub (repo not yet initialised) | |

---

## 8. Development environment setup

| Item | Detail |
|---|---|
| OS | Ubuntu 22.04.5 LTS (Linux 6.8) |
| System Python | 3.10.12 (`/usr/bin/python3`). Python 3.7 also exists but is not used |
| Why `virtualenv` | `python3 -m venv` fails because `python3.10-venv`/`ensurepip` is not installed (needs sudo). The already-installed `virtualenv` was used instead |
| venv | `/home/aditya/gisproject/.venv` (pip 26.3) |
| Installed packages | `requests`, `pillow` (+ dependencies) |
| QGIS | Flatpak `org.qgis.qgis//lts` v3.28.9, user install (Flathub remote added with `--user`). Has full filesystem access |
| Launch QGIS | Super key → "QGIS", or `flatpak run org.qgis.qgis//lts` |
| Chrome | `/usr/bin/google-chrome` (for mockups). Firefox and Zen browser also installed |
| Node.js / npm | **v20.20.2 / 10.8.2** installed (enough for React + Vite) |
| Git | v2.34.1 installed; the folder is **not** a git repo yet (don't init unless asked) |
| sudo | Assume **no sudo** for the agent; prefer user-level installs (pip in the venv, `flatpak --user`, npm locally) |

Recreate the venv from scratch:
```bash
cd /home/aditya/gisproject
python3 -m virtualenv -p python3.10 .venv
.venv/bin/pip install -r requirements.txt
```

---

## 9. Data sources and APIs (with live status)

Status as checked on **24 Nov 2026** from this machine.

| # | Data | Source / API | Access | Status | Used for |
|---|---|---|---|---|---|
| 1 | District boundary | **Nominatim** `https://nominatim.openstreetmap.org/search?q=Chamoli district, Uttarakhand, India&format=jsonv2&polygon_geojson=1` | Free; needs a User-Agent; max 1 request/s | ✅ Works | Boundary polygon, bbox, relation id |
| 1b | Boundary fallback | Overpass relation search, then Nominatim `/lookup?osm_ids=R<id>` | Free | (fallback, not needed) | |
| 2 | Roads | **Overpass API** (`way(area)["highway"~...]; out body geom;`) | Free | ✅ `overpass-api.de` (sometimes 502s) and ✅ `maps.mail.ru/osm/tools/overpass/api/interpreter`. ❌ `overpass.kumi.systems` and `overpass.private.coffee` timed out | 1,226 ways → 5,820 segments |
| 3 | Points of interest | Overpass (`amenity=hospital/clinic/doctors/police/fuel`, `healthcare=*`, `emergency=ambulance_station`) | Free | ✅ | 122 POIs |
| 4 | Rivers and streams | Overpass (`waterway=river|stream`) | Free | ✅ | 61 rivers + 807 streams |
| 5 | Landslides: NASA COOLR (live) | ArcGIS REST `gis.earthdata.nasa.gov/gis05/.../COOLR_Reports_Points/{MapServer,FeatureServer}`, `maps.nccs.nasa.gov/...` | Free | ❌ **Dead** (404 / DNS failure) | Tried first, then the fallback |
| 5b | Landslides: NASA Global Landslide Catalog | CSV `https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv` (8.5 MB) | Free | ✅ (events **2007–2017** only) | 41 points in Chamoli (23 accurate enough to use) |
| 6 | Landslides: news (web research) | Hand-built `data/manual/web_landslides.csv` (see §16) | — | ✅ 40 events (37 located) | 2021–2025 events |
| 7 | Landslides: GSI inventory + susceptibility (NLSM) | **GSI Bhukosh** `https://bhukosh.gsi.gov.in` (register → cart → emailed shapefiles) | Free, manual | ❌ **Website timing out** (24 Nov 2026). The main GSI site `gsi.gov.in` works | Planned: `data/manual/gsi_landslides.geojson`, `gsi_susceptibility.geojson` |
| 8 | GSI landslide forecast bulletins | `http://www.bhusanket.gsi.gov.in/` | Free, PDF/web, no API | ✅ Reachable (slow) | Phase 2, entered by hand |
| 9 | Weather | **Open-Meteo Forecast** `https://api.open-meteo.com/v1/forecast` (hourly precipitation, rain, snowfall, visibility, weather_code; `past_days=3`, `forecast_days=3`, `timezone=Asia/Kolkata`); all 10 towns in **one call** | Free, no key, non-commercial | ✅ | Rain past 72 h / next 24 h → rain factor |
| 10 | Elevation (default) | **AWS Terrain Tiles** (Terrarium PNG) `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`, zoom 12 (~33 m/pixel in Chamoli). Decoding: `elev = R*256 + G + B/256 − 32768` | Free, no key, no rate limit | ✅ (80 tiles cover all roads) | 23,075 elevation points |
| 10b | Elevation (fallback) | **Open-Meteo Elevation** `https://api.open-meteo.com/v1/elevation` (~90 m, 100 points per call) | Free; **600 points/min, ~10k/day** | ⚠️ Rate-limited | `--elev-source open-meteo`, paced at 100 points every 10 s |
| 11 | 30 m DEM GeoTIFF | **OpenTopography** `https://portal.opentopography.org/API/globaldem?demtype=COP30&...&API_Key=KEY` | Free key needed | ⏸ Not set up (no key) | For a proper slope raster in QGIS → `output/dem_cop30.tif` |
| 12 | Live incidents | TomTom Traffic Incidents v5 (bbox ≤ 10,000 km², so it's split into tiles) / HERE v7 | Free developer key | ⏸ Not set up (no key); coverage likely poor | Optional |
| 13 | Thematic layers | ISRO Bhuvan WMS `https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms` | Free | Not used yet | Display only |
| 14 | Google Maps | — | — | ❌ Not used (D12) | — |
| 15 | IMD API | `https://api.imd.gov.in` | Needs IP whitelisting | Not used (Open-Meteo first) | Possible upgrade later |

**Rate-limit etiquette built into the script:** response caching, retries with backoff, Overpass mirror fallback, ≥ 1.1 s between Nominatim calls, a polite User-Agent, and Open-Meteo pacing.

---

## 10. Folder and file guide

```
gisproject/
├── SAFEYATRA_FULL_CONTEXT.md        ← THIS FILE: complete context and status
├── project_context.md               ← Original hand-off spec (A–Z design doc, written before work began)
├── requirements.txt                 ← Python packages (requests, Pillow; phase-2 packages commented out)
├── .env.example                     ← Template for optional keys: CONTACT_EMAIL, OPENTOPO_API_KEY, TOMTOM_API_KEY
├── .gitignore                       ← Ignores .venv/, __pycache__/, .env, cache/, output/, data/raw/
├── .venv/                           ← Python 3.10 virtual environment (~40 MB). Do not edit by hand
│
├── scripts/
│   ├── fetch_chamoli_data.py        ← STEP 1 data pipeline (~1,580 lines). Fetches everything, computes
│   │                                   segment attributes and the preview risk, writes output/. See §11
│   ├── make_mockups.py              ← Renders the 11 app mockup PNGs from real data, with real A* routes. See §17
│   └── __pycache__/                 ← Python bytecode cache (auto-generated, ignore)
│
├── data/
│   ├── manual/                      ← Hand-made or downloaded input datasets the script reads
│   │   ├── web_landslides.csv       ← 40 landslide events (2021–25) from web research, located on the map (§16)
│   │   ├── accidents.csv            ← Headers only (accident feature dropped, D4). Keeps the loader quiet
│   │   ├── accidents.example.csv    ← Template showing the accident CSV format (2 fake example rows)
│   │   ├── (gsi_landslides.geojson)     ← TO ADD when GSI Bhukosh data arrives (EPSG:4326)
│   │   └── (gsi_susceptibility.geojson) ← TO ADD when GSI Bhukosh data arrives (EPSG:4326)
│   └── raw/                         ← Empty; for big raw files (DEM tiles, .pbf). Git-ignored
│
├── cache/                           ← ~26 MB, ~112 files. Cached API responses (SHA-1 of URL+params),
│                                       including 80 elevation tiles. Delete or use --refresh to re-download
│
├── output/                          ← ~16 MB. Generated by fetch_chamoli_data.py (git-ignored). See §12
│   ├── boundary.geojson             ← District polygon + metadata
│   ├── roads_segments.geojson       ← 5,820 road segments with ALL attributes + risk (main deliverable)
│   ├── segments.csv                 ← Same attributes as a table, geometry as WKT (opens in Excel/QGIS)
│   ├── landslides.geojson           ← 78 landslide points (41 NASA + 37 news)
│   ├── rivers.geojson               ← 61 rivers + 807 streams
│   ├── pois.geojson                 ← 122 hospitals/clinics/police/fuel/ambulance points
│   ├── accidents.geojson            ← Empty FeatureCollection (feature dropped)
│   ├── weather.json                 ← Per-town rain/snow/visibility + rain factor
│   └── summary.json                 ← Run summary: counts, risk preview, sanity checks, warnings
│   (dem_cop30.tif, incidents.json   ← only appear if the OpenTopography / TomTom keys are set)
│
├── qgis/
│   └── safeyatra.qgz                ← QGIS project saved by the user (layers styled, basemap)
│
└── app images for future reference/ ← 11 mockup PNGs of the planned app + README.md index (§17)
```

---

## 11. The data pipeline: `fetch_chamoli_data.py`

**Purpose:** one script that pulls every dataset available through APIs, loads the hand-made datasets, splits roads into segments, computes all per-segment attributes and a preview risk score, **prints a JSON summary to stdout** (progress goes to stderr) and writes all files to `output/`.

### Command-line options
```
python scripts/fetch_chamoli_data.py
  [--only boundary,roads,pois,rivers,landslides,weather,elevation,incidents,dem,manual]
  [--segment-length 500]          # max segment length in metres
  [--road-classes main|all]       # main = motorway..tertiary (+links); all = + unclassified, residential (default all)
  [--elev-source tiles|open-meteo]# default tiles
  [--max-elev-points 5000]        # budget, only for open-meteo
  [--full]                        # print the full summary (default prints a top-5 instead of top-10)
  [--refresh]                     # ignore the cache, re-download everything
  [--out output/]
```
The boundary step always runs, because every other step needs it.

### Steps (in order)

| Step | What it does | Key details |
|---|---|---|
| 1. Boundary | Nominatim search → picks `osm_type=relation` + `category=boundary`; fallback: Overpass relation, then Nominatim lookup | Computes area (shoelace formula on a local projection) and bbox |
| 2. Roads | Overpass, `out body geom` (node ids + geometry) | Keeps highway, name, ref, surface, lanes, width, maxspeed, oneway, bridge, tunnel |
| 3. POIs | Overpass `out center tags` | Categories: hospital, clinic, doctors, police, fuel, ambulance, healthcare_other |
| 3b. Rivers | Overpass `waterway=river|stream` | kind, name, length |
| 4. Landslides (NASA) | Tries the COOLR ArcGIS layers (paginated); if offline, downloads the GLC CSV (parsed with `io.StringIO`, because descriptions contain newlines), filters to the bbox and then the district polygon | Normalised to the landslide schema: id, source, event_date, category, trigger, fatalities, description, location_precision |
| 5. Manual datasets | Loads `web_landslides.csv`, `gsi_landslides.geojson` (polygon → centroid), `gsi_susceptibility.geojson` (auto-detects the class field: first key containing "susc" or "class"; maps Low/Moderate/High/Very High or 1–4), `accidents.csv` | Missing files → a warning, and the step is skipped |
| 6. Weather | One Open-Meteo call for the 10 towns | rain_past_72h_mm, rain_next_24h_mm, snow_next_24h_cm, min_visibility_m, weather_code_now, rain_factor |
| 7. Segmentation | Splits each way at **junction nodes** (nodes shared with other ways, plus way ends), then into pieces ≤ segment length, **cutting only at existing vertices** | Every segment starts and ends on a real OSM node: `u_node`, `v_node` (needed for the graph). id format `w<wayid>_s<NNN>` |
| 8. Elevation | For each segment, samples **start, mid, end** plus **left/right points 100 m either side of the midpoint** | gradient_avg_pct, gradient_max_pct, elev_start/end/min/max, **cross_slope_deg** = atan(\|e_left − e_right\| / 200 m) as a stand-in for terrain slope. Points are deduplicated at 4 decimals; main roads go first if there's a budget |
| 9. Geometry | Drops vertices closer than 10 m apart, sums heading changes | curvature_deg_per_km, sharp_turns (heading change > 60°) |
| 10. Proximity | Local projection + bounding-box pre-filter | landslides_within_500m, nearest_landslide_m (only precise landslides, D8), accidents_within_500m (severity-weighted), is_black_spot (≤ 250 m), nearest_hospital_m (hospital + clinic), nearest_weather_point, landslide_susc_class (max at start/mid/end) |
| 10b. Rivers | `PieceGrid` = a simple 1 km grid spatial index over river line pieces; widens the search ring by ring until it finds the nearest river | dist_to_river_m (exact line-to-line distance; 0 when a bridge crosses), stream_crossings (count of distinct streams intersecting the segment) |
| 11. Preview risk | Weighted sum (§13); factors without data are dropped and their weight shared out | static_risk, risk_class, risk_factors, dynamic = 1, risk_now = static_risk, closed = False |
| 12a. Incidents | TomTom (only if `TOMTOM_API_KEY` is set); bbox split into tiles under 9,000 km² | incidents.json |
| 12b. DEM | OpenTopography COP30 (only if `OPENTOPO_API_KEY` is set) | output/dem_cop30.tif |
| 13. Output + sanity checks | Writes the files (§12) and summary.json; prints the summary | Checks: area within ±20% of 7,700; bbox inside the expected box (±0.05°); total road km 200–10,000; NH-7 continuity Karnaprayag→Badrinath (breadth-first search over NH-7 segments); elevation at Karnaprayag and Badrinath; nearest town of each landslide; weather values non-negative |

### Internals worth knowing
- **`Http` class:** session with User-Agent; disk cache in `cache/` keyed by SHA-1 of (method, url, params, data); retries on 429/502/503/504 with 2 s and 4 s backoff; Nominatim throttle; `overpass()` tries each mirror in turn.
- **Geometry helpers (pure Python):** haversine, bearing, offset_point, LocalProjection, point_segment_dist, point_in_ring / point_in_geometry (ray casting, MultiPolygon + holes), geometry_area_km2, centroid, point_along, segments_intersect, piece_piece_dist.
- **`.env` loader:** a tiny built-in KEY=VALUE parser (no python-dotenv needed).
- Runtime: first run about 5 min (Overpass is slow); later runs about 30–90 s from the cache.

---

## 12. Output files and their fields

### `roads_segments.geojson` / `segments.csv` (one row per segment)

| Field | Meaning |
|---|---|
| segment_id | `w<osm_way_id>_s<NNN>` |
| osm_way_id, u_node, v_node | Parent OSM way; start and end OSM node ids (graph endpoints) |
| highway, name, ref, surface, lanes, width, oneway, bridge, tunnel | OSM tags |
| length_m | Segment length (haversine) |
| elev_start_m, elev_end_m, elev_min_m, elev_max_m | Elevation samples |
| gradient_avg_pct, gradient_max_pct | Road steepness from elevation |
| cross_slope_deg | Terrain steepness across the road (±100 m sampling) |
| curvature_deg_per_km, sharp_turns | Bendiness and hairpin count |
| landslide_susc_class | 1–4 from GSI (currently empty) |
| landslides_within_500m, nearest_landslide_m | Landslide exposure (precise records only) |
| accidents_within_500m, is_black_spot | Always 0/false (feature dropped) |
| dist_to_river_m, stream_crossings | River erosion / nala exposure |
| nearest_hospital_m | Distance to the nearest hospital or clinic |
| nearest_weather_point | Town id whose weather applies |
| static_risk, risk_class | Preview risk 0–1 and its class |
| risk_factors | (GeoJSON only) the normalised factor values used |
| dynamic, risk_now, closed | Placeholders for phase 2 (1.0, = static_risk, false) |
| wkt | (CSV only) LINESTRING geometry |

### Others
- **landslides.geojson:** id, source (NASA_GLC / NEWS / GSI), event_date, category, trigger, fatalities, description, location_precision, (source_url for news).
- **rivers.geojson:** osm_id, kind (river/stream), name, length_m.
- **pois.geojson:** id, osm_id, category, name, phone.
- **weather.json:** point_id, name, lat, lon, fetched_at, rain_past_72h_mm, rain_next_24h_mm, snow_next_24h_cm, min_visibility_m, weather_code_now, rain_factor.
- **summary.json:** generated_at, study_area, datasets (roads, landslides, accidents, pois, rivers, weather, incidents, dem), risk_preview (by_class_km, top_10_segments), sanity_checks, warnings.

---

## 13. Risk model

### Normalisation (each factor scaled 0–1)

| Factor | Formula (v1) | Source field |
|---|---|---|
| Susceptibility | class 1→0.1, 2→0.4, 3→0.7, 4→1.0 | landslide_susc_class (GSI, **missing**) |
| Landslide density | min(landslides_within_500m / 5, 1) | landslides |
| Terrain slope | min(cross_slope_deg / 45, 1); fallback min(gradient_avg_pct / 12, 1) | elevation |
| Curvature | min(curvature_deg_per_km / 1500, 1) | road geometry |
| Accident density | min(weighted / 5, 1), black spot → ≥ 0.8 | **dropped** |

Later: switch to percentile scaling (95th percentile = 1.0) once all the data is in.

### Static risk (weights from the spec, §10.4)
```
static_risk = 0.30·susceptibility + 0.20·landslide_density + 0.20·terrain_slope
            + 0.15·curvature + 0.15·accident_density
```
Factors without data are **left out and the weights re-normalised**: `risk = Σ(w·f) / Σ(w of available factors)`.
**Currently active:** landslide_density (0.20), terrain_slope (0.20), curvature (0.15), so the effective weights are 0.364 / 0.364 / 0.273.

**Risk classes:** low < 0.25 ≤ medium < 0.5 ≤ high < 0.75 ≤ very_high.

Alternatives to mention in the report: weights via **AHP (Analytic Hierarchy Process)**; a trained model (logistic regression / random forest) later.

### Dynamic multiplier (phase 2, hourly)
```
dynamic = 1 + rain_factor + gsi_alert_factor (+ night_factor + fog_snow_factor optional)
risk_now = landslide_part · (1 + rain_factor + gsi_alert_factor)
         + other_part     · (1 + night_factor + fog_snow_factor)
```
| Nearest town's weather | rain_factor |
|---|---|
| next-24 h < 10 mm and past-72 h < 30 mm | 0 |
| next-24 h 10–35 mm or past-72 h 30–75 mm | 0.3 |
| next-24 h 35–65 mm or past-72 h 75–150 mm | 0.6 |
| next-24 h > 65 mm or past-72 h > 150 mm | 1.0 |

gsi_alert_factor: none 0 / low 0.3 / moderate 0.6 / high 1.0. (Already implemented: the `rain_factor()` function, and the per-town values in weather.json.)

### Hard rules (phase 2)
- Verified blockage or closure → the road is removed from the graph (cost = ∞).
- Seasonal closure (date-based) → removed in that date range.
- Unverified user report → temporary penalty (risk += 0.3, expires after 6 h unless confirmed).

### Candidate additions
- River factor (e.g., `dist_to_river_m < 100` → +), stream crossings, GSI forecast. Each is a small change in `add_static_risk()`.

---

## 14. Current results (latest run)

Generated 24 Nov 2026, 18:08 IST.

| Metric | Value |
|---|---|
| Boundary | relation 374815, **7,832.7 km²**, bbox [79.076, 29.9256, 80.102, 31.0723] ✅ |
| Roads | **1,226 ways → 5,820 segments, 2,331.5 km** ✅ |
| Road km by class | unclassified 1,372.8 · tertiary 429.7 · trunk 353.0 · primary 91.2 · secondary 51.4 · residential 33.3 |
| NH-7 | found, 177.3 km, **continuous Karnaprayag → Badrinath** ✅ |
| Elevation | all 5,820 segments; Karnaprayag **767 m**, Badrinath **3,125 m** ✅ (23,075 points, 80 tiles) |
| Landslides | **78** total: 41 NASA GLC + 37 news; **60** precise enough for risk |
| Landslides by nearest town | Nandprayag 14, Joshimath 12, Pipalkoti 12, Karnaprayag 11, Govindghat 10, Chamoli 8, Badrinath 8, Tharali 2, Gopeshwar 1 |
| POIs | clinic 92, hospital 13, fuel 12, police 4, healthcare_other 1 (122 total) |
| Rivers | 61 rivers (740 km), 807 streams (2,387 km) |
| Weather | 0 mm everywhere (late November, dry season) ✅ |
| Risk preview | **low 511.8 km · medium 1,746.9 km · high 71.9 km · very high 0.9 km** |
| Riskiest NH-7 stretch | **Nandprayag** (risk 0.76, very high: 6 landslides within 500 m, slope 40°, river 96 m away); matches news reports of repeated blockages |
| Attribute distributions | cross_slope median 22° (95th pct 39°); curvature median 636°/km (95th 1,374); gradient median 5.3% (outliers up to 239% on very short segments); nearest hospital median 1.95 km |
| Remaining warnings | NASA COOLR offline (fallback used); GSI inventory and susceptibility files not found; OPENTOPO_API_KEY not set |

---

## 15. Rivers report

| Item | Value |
|---|---|
| River lines | 61 (740.1 km) |
| Stream (*nala*) lines | 807 (2,386.5 km) |
| Rivers by length | Alaknanda 124.0 km · Pindar 75.4 (+ "Pindar River" 28.3) · Dhauli Ganga 61.4 · Nandakini 56.7 · Saraswati 39.8 · Kail Ganga 34.7 · Rishi Ganga 32.6 · Ramganga 30.3 · Birahi Ganga 29.9 · Kalpa Ganga 18.9 · unnamed 21.0 |
| Road km within 100 m of a river | **363.2** |
| Road km within 250 m | 682.9 |
| Road km within 500 m | **911.7** (~40% of all roads) |
| Segments with stream crossings | 322 (335 crossings in total) |

**Why it matters:** rivers wear away the bottom of the slope (toe erosion), so riverside roads slide more often. Stream crossings are where monsoon debris flows and culvert washouts block roads. OSM stream mapping is incomplete in remote areas.

---

## 16. Landslide dataset from web research

**File:** `data/manual/web_landslides.csv`
**Columns:** id, lat, lon, event_date, place, type, fatalities, description, location_precision, location_method, source, source_url

- **40 events, 2021–2025** (plus one undated "chronic zone" row), compiled from news reports (Tribune, Deccan Herald/PTI, Organiser, AIR/newsonair, LatestLY, Lokmat Times, Telangana Today, News Arena, Daily Pioneer, India TV, Amar Ujala) and one journal paper (Shugar et al. 2021, *Science*, on the Rishiganga disaster).
- **Types:** landslide, debris_fall, debris_flow, rockfall, rock_ice_avalanche, flood_debris, chronic_zone.
- **Places by number of reports:** Nandprayag 5 · Bhanerpani 4 · Lambagad (Khachda nala) 3 · Pagal Nala 3 · Kameda 3 · Helang 2 · Patalganga 2 · Chatwapipal 2 · Gulabkoti · Hanuman Chatti · Chhinka · Sonala · Umatta · Joshimath · Thaing · Raini · Tharali (Ming Gadhera, Kotdeep) · Nandanagar (Kuntari Lagaphali, Sera) · Dhurma.
- **Major disasters included:** Rishiganga/Raini rock-ice avalanche (7 Feb 2021, over 200 dead or missing) · Tharali cloudburst (23 Aug 2025) · Nandanagar debris flows (18 Sep 2025, toll 7) · Chatwapipal rockfall (2024, 2 killed).

**How locations were found:**

| location_precision | Count | Method |
|---|---|---|
| stream-crossing | 8 | Point where NH-7 crosses the named OSM stream: Pagal Nala (30.47977, 79.46787), Patal Ganga (30.48755, 79.48611), Khachar Gadhera = Khachda drain near Lambagad (30.64892, 79.52397) |
| village-level | 14 | OSM village/hamlet (Nominatim / Overpass); highway events moved to the nearest point on NH-7 |
| approximate | 15 | Not in OSM; placed from the report's wording: Bhanerpani "near Pipalkoti", Kameda "near Gauchar", Chatwapipal "halfway between Gauchar and Karnaprayag", Helang "between Gulabkoti and Joshimath (~35%)", Sonala (OSM "SubCentre, Sonla", 2 km off), Kotdeep → Tharali, Kuntari/Sera → Nandanagar (Ghat) PHC. About 2–5 km uncertainty |
| not_located | 3 | Parthadeep, Barrage Kunj, Bairagana: kept in the file, skipped by the loader |

**Notes:** Nandanagar's old name is **Ghat**. OSM's "Lambagad" point (30.6926) sits next to Hanumanchatti and looks misplaced, so the Khachda crossing was used instead. **Reporting bias:** news over-represents busy places (e.g., Nandprayag), so the GSI inventory is needed for balance.

---

## 17. App mockups

**Folder:** `app images for future reference/` (11 PNGs + README.md)
**Made by:** `scripts/make_mockups.py`, which renders HTML + SVG and screenshots it with headless Chrome. Chrome loses about 87 px of height, so the script renders 200 px taller and crops with Pillow.
**Uses real data:** the actual roads coloured by risk, real landslides, rivers and POIs, and **real A\* routes**. Re-run it after the data changes.

| Image | Screen | Phase |
|---|---|---|
| 01_home_risk_map.png | Home: district risk map + km per risk class | MVP |
| 02_route_search.png | Place search with suggestions, popular routes | MVP |
| 03_route_comparison_safety_slider.png | Safety slider; **Karnaprayag → Gopeshwar**: safest 41.5 km / 1 h 42 vs shortest 39.8 km / 1 h 09; 27% less high-risk road; the safe route avoids the NH-7 stretch between Nandprayag and Chamoli (Sonala, Chhinka) | MVP |
| 04_route_risk_breakdown.png | **Gopeshwar → Joshimath** (59.2 km, 1 h 42, risk 0.35, one road only): risk + elevation profile, 10 dangerous stretches | MVP |
| 05_hazard_layers.png | Layer switches; Pipalkoti–Joshimath valley; NASA vs news landslides | MVP |
| 06_road_segment_details.png | Clicked segment near Nandprayag: risk 0.76 + factor bars | MVP |
| 07_weather_alerts.png | Heavy-rain + GSI alert, town rain table, map on an **example** monsoon day (made-up rain numbers) | Phase 2 |
| 08_nearest_help.png | Hospitals, clinics, police, fuel along the route; emergency numbers 108 / 112 / 1070 | Phase 3 |
| 09_report_blockage.png | Report form (landslide at Pagal Nala, photo) | Phase 2 |
| 10_admin_panel.png | Reports table (verify/reject), closures (e.g., Badrinath–Mana snow 15 Nov – 30 Apr). Example data | Phase 2 |
| 11_mobile_view.png | Phone layout with bottom sheet | Phase 3 |

Mockup design system: navy header `#14213d`, accent `#f5b301`, primary blue `#1d5fd1`. Risk colours: low `#2e9d5b`, medium `#e0b000`, high `#ee7a10`, very high `#d62828`. Landslides are purple triangles `#7b3fa0` (news ones `#c2185b`).
Estimated travel speeds used: trunk 35 km/h, primary 30, secondary 25, tertiary 20, others 15.

---

## 18. Data inventory: what we have and what we lack

### ✅ Have (12)
1. District boundary
2. Road network (2,332 km, 5,820 segments)
3. Elevation for every segment (~30 m tiles)
4. Road gradient
5. Road bends + sharp turns
6. Hospitals / clinics / police / fuel (122) + distance to nearest hospital
7. Weather, live (10 towns)
8. Rivers (61) + distance to river
9. Streams (807) + stream crossings
10. Past landslides: NASA (41, 2007–2017)
11. Past landslides: news (40 events, 2021–2025)
12. Preview risk score for every segment

### ⚠️ Have, but could be better (2)
13. **Terrain slope**: currently estimated from two points beside each segment. Fix: a proper slope raster (from the terrain tiles or the OpenTopography DEM), then zonal statistics in a 50 m buffer. **Claude can do this without any key.**
14. **Landslide locations**: 15 news events are approximate; news has reporting bias. Fix: the GSI inventory.

### ❌ Missing for the main version (2)
15. **GSI landslide susceptibility zones (NLSM)**: 30% weight, **the biggest gap**. Bhukosh website down; retry.
16. **GSI landslide inventory**: same request.

### ❌ For later (3)
17. GSI daily landslide forecast (monsoon; entered by hand)
18. Seasonal road closures (entered by hand)
19. Live incidents (TomTom, optional, needs a key)

### 🚫 Dropped (1)
- Accidents (D4)

---

## 19. App design: how it will work

```
┌──────────── DATA (output/) ────────────┐
│ roads_segments + risk, landslides,      │
│ rivers, POIs, weather                   │
└───────────────────┬─────────────────────┘
                    ▼  loaded at startup
┌──────────── BACKEND (FastAPI) ─────────┐        hourly
│ NetworkX graph in memory               │ ◀── weather updater (Open-Meteo)
│ A* with cost = length·(1 + λ·risk)     │ ◀── closures / verified reports
│ /route /segments /hazards /pois ...    │
└───────────────────┬─────────────────────┘
                    ▼  JSON / GeoJSON
┌──────────── FRONTEND (React + Leaflet) ┐
│ search · safety slider · route cards    │
│ risk-coloured map · warnings · report   │
└─────────────────────────────────────────┘
```

**User flow:** choose start and destination → move the safety slider → **Find route** → see the safe and shortest routes, their distance, time and risk → read the dangerous stretches, rain alerts and nearest hospitals → (optional) report a blockage.

---

## 20. Routing (A*) design

- **Graph:** nodes are road junctions and segment endpoints (`u_node`, `v_node` with coordinates); edges are segments. Directed, respecting `oneway` (rare in Chamoli); in practice both directions for most roads.
- **Edge attributes:** length_m, travel_time_s, static_risk, dynamic, risk_now, closed.
- **Travel time:** `length / speed`. Default hill speeds if `maxspeed` is missing: trunk 35 km/h, primary 30, secondary 25, tertiary 20, unclassified/residential 15, track 10.
- **Edge cost:**
  ```
  cost(e) = length_m(e) · (1 + λ · risk_now(e))   if not closed
  cost(e) = ∞                                      if closed
  ```
  λ: 0 = pure shortest; UI presets 0 / 2 / 5 / 10 = Fastest / Balanced / Safe / Safest. Variant: use travel_time_s as the base.
- **Heuristic:** `h(n) = haversine(n, goal)`. Because cost ≥ length ≥ straight-line distance, **the heuristic is admissible**, so A\* returns the optimal path for the given λ (a good viva point).
- **Snapping:** the start and end points snap to the nearest node on a main road (trunk–tertiary), to avoid tiny disconnected bits of road.
- **Output per route:** GeoJSON LineString, distance_km, est_time_min, route_risk_avg (length-weighted), route_risk_max, hazard_stretches[] (consecutive high/very-high segments with start/end km and reasons), comparison with λ = 0 (extra_km, risk_reduction_pct).
- **Prototype already exists** inside `scripts/make_mockups.py` (`astar()` with heapq): it produced the Karnaprayag→Gopeshwar and Gopeshwar→Joshimath routes.

---

## 21. Backend API design

| Method and path | Purpose | Params → response |
|---|---|---|
| GET /health | Health check | |
| GET /places?q= | Search Chamoli places (local list + Nominatim fallback) | `[{name, lat, lon}]` |
| GET /route | Safe route | `from=lat,lon&to=lat,lon&safety=0..10&avoid_night=bool` → `{safe_route, shortest_route, comparison, hazard_stretches, weather_alerts, nearest_help}` |
| GET /segments | Risk-coloured road layer | `bbox=&min_risk=` → GeoJSON FeatureCollection |
| GET /hazards | Landslides (+ rivers) | `type=landslide&bbox=` |
| GET /weather | Current rain risk per town | |
| GET /pois | Hospitals/police/fuel | `bbox=&category=` |
| POST /reports | User report | `{type, lat, lon, description, photo}` |
| GET /admin/reports, PATCH /admin/reports/{id} | Verify/reject (auth) | |
| POST /admin/closures | Add a closure (auth) | |

On startup: load roads_segments into a NetworkX graph. The hourly job updates dynamic / risk_now / closed in memory.

Data for phase 2 (reports, closures): simple JSON/SQLite storage is fine at college level.

---

## 22. Frontend design

- **Layout:** full-screen map + left panel (desktop) / bottom sheet (mobile).
- **Panel:** From / To search → safety slider → **Find route** → result cards (Safe vs Shortest: km, time, risk badge) → dangerous stretches list (click to zoom) → weather alert banner → nearest hospitals.
- **Map layers:** risk-coloured roads (green / yellow / orange / red), landslide points, rivers, district boundary, optional slope. Legend + layer switches.
- **Report button:** floating "⚠ Report blockage" → pick a location → type → optional photo.
- **Accessibility:** colour-blind-friendly palette with text labels, large tap targets, Hindi/English toggle.
- **Performance:** simplify geometries for the web if the layers get large.
- **Reference visuals:** see `app images for future reference/`.

---

## 23. Implementation plan and phase status

| Phase | Deliverables | Owner | Status |
|---|---|---|---|
| **0. Setup** | venv, folders, requirements, .env.example, .gitignore, QGIS installed | All | ✅ Done (git not yet initialised) |
| **1. Data collection** | `fetch_chamoli_data.py` end to end; summary passes the sanity checks | GIS | ✅ Done (GSI pending) |
| 1+. Extra data | Rivers + streams; news landslide dataset | GIS | ✅ Done |
| **2. Data preparation (QGIS / GeoPandas)** | Proper slope raster (EPSG:32644), zonal stats in a 50 m buffer, clipped/cleaned layers, `road_segments.gpkg` | GIS | ⏳ Next (slope can start now) |
| **3. Maps** | Boundary, roads, elevation, slope, landslide, river, risk maps (QGIS layouts → PNG/PDF) | GIS | ⏳ Partly (QGIS project saved; layouts not yet made) |
| **4. Risk attributes (final)** | All attributes + static_risk with GSI susceptibility; validation | GIS | ⏳ Waiting for GSI |
| **5. Routing prototype** | Graph + A\* + λ; demo routes | Backend | ✅ Done (`backend/app/routing.py`, tests) |
| **6. API** | FastAPI `/route`, `/segments`, `/hazards`, `/pois` + tests | Backend | ✅ Done (`backend/app/main.py`) |
| **7. Frontend MVP** | Map + search + slider + route cards + risk layer | Frontend | ✅ Done (`frontend/`) |
| **8. Live layers** | Weather updater, GSI alert input, reports + admin | Backend + Frontend | ✅ Done (needs Clerk key for reports/admin) |
| **9. Validation and report** | Metrics, screenshots, documentation, presentation | All | ⬜ |
| **10. Expansion** | More districts, mobile, offline | — | Future |

### Rough timeline (from the app design discussion)
| Step | Time |
|---|---|
| Finish data (slope + GSI) | 1–2 weeks (mostly waiting for GSI) |
| Routing test notebook | 2–3 days |
| Backend | 1 week |
| Frontend | 1–2 weeks |
| Extras (live rain, hospitals, warnings) | 1 week |
| Testing, screenshots, report | 1 week |

### Immediate next steps (summary; **full detail with "done when" checks in §32**)
1. **Claude:** proper slope map (from the cached terrain tiles or the OpenTopography DEM) → better terrain_slope.
2. **Claude:** routing test notebook (`notebooks/03_astar_prototype.ipynb` or a script) on the demo routes.
3. **User:** retry GSI Bhukosh every few days; when the data arrives, export to GeoJSON (EPSG:4326) in `data/manual/` and re-run the script.
4. Then: backend → frontend.

---

## 24. Validation and testing plan

- **Hold-out test:** keep back 20–30% of landslide points (e.g., the most recent years); check what % fall on or near high / very-high segments (success-rate / ROC per class).
- **Known hotspots check:** chronic NH-7 zones (Pagal Nala, Patalganga, Helang, Lambagad, Nandprayag, Bhanerpani, Kameda) should score high. **Currently Nandprayag scores very high (0.76).**
- **Sensitivity analysis:** vary the weights by ±0.05 and check how stable the top-risk rankings are.
- **Routing tests:** λ = 0 equals the plain shortest path; increasing λ never increases route risk; closed edges are never used; heuristic admissible (h ≤ true cost).
- **Unit tests:** segment lengths add up to the way length; haversine; point-in-polygon; curvature on synthetic lines; risk bounds [0, 1].
- **Visual check in QGIS** of every exported layer.
- **Sanity checks** are already automated in summary.json (§11, step 13).

---

## 25. Known limitations and caveats

| Issue | Impact | Mitigation |
|---|---|---|
| GSI Bhukosh down | Biggest risk factor (susceptibility, 30%) missing | Weight shared out; NASA + news landslides as a stand-in; retry |
| NASA GLC stops in 2017; COOLR endpoints dead | Old, sparse landslide data | News dataset 2021–25 added |
| News dataset: approximate locations, reporting bias | Busy places over-counted | Flagged `location_precision`; GSI will balance it |
| Terrain slope from point sampling | Coarser than raster zonal statistics | Proper slope raster next |
| DEM 30 m on hairpins | Road gradient noisy; outliers (239%) on very short segments | Treat as terrain proxy; GeoPandas pipeline will clean it |
| Few alternative roads | Safe route often = shortest | Present as risk-aware routing + warnings |
| OSM gaps on village roads and streams | Incomplete graph / crossings | Flag low-quality classes; fix in QGIS if needed |
| Roads extend slightly beyond the boundary (not clipped) | Minor | Clip in phase 2 (QGIS/GeoPandas) |
| Static weights subjective | Questioned in viva | Justify (literature / AHP); sensitivity analysis |
| Open-Meteo free tier non-commercial | Licence limit | Fine for an academic project |
| Overpass/Nominatim rate limits | Blocked requests | Cache, mirrors, User-Agent, delays |
| Accident component dropped | No accident layer | Bends and sharp turns as the road-danger stand-in |
| Live blockages lack API coverage | No real-time closures | User reports + admin panel (phase 2) |
| QGIS Flatpak LTS branch outdated (3.28.9) | Older UI/features | Works for this project; "stable" branch available |

---

## 26. Licensing and attribution

- **OpenStreetMap** (roads, rivers, POIs, boundary): ODbL. Show "© OpenStreetMap contributors".
- **AWS Terrain Tiles** (Mapzen/Tilezen, SRTM-based in this region): attribute the terrain tile sources (Mapzen/Tilezen, SRTM/NASA).
- **Copernicus DEM** (if used): "© DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA".
- **Open-Meteo**: CC BY 4.0, non-commercial. "Weather data by Open-Meteo.com".
- **NASA Global Landslide Catalog**: cite Kirschbaum, D.B., Stanley, T., & Zhou, Y. (2015), *Spatial and temporal analysis of a global landslide catalog*, Geomorphology 249, 4–15; and Juang, Stanley & Kirschbaum (2019), COOLR, PLOS ONE 14(7): e0218657.
- **News sources**: cite each URL in the `source_url` column of `web_landslides.csv`.
- **Rishiganga disaster**: Shugar et al. (2021), *Science*, doi:10.1126/science.abh4455.
- **GSI Bhukosh** (when used): accept the terms; cite GSI.
- **ISRO Landslide Atlas / Bhuvan** (if used): cite NRSC/ISRO.
- **TomTom/HERE** (if used): follow their developer terms.

---

## 27. Open tasks (who does what)

### User
- [ ] Retry **GSI Bhukosh** (https://bhukosh.gsi.gov.in) every few days, from a different network if needed (mobile data / college Wi-Fi), with any VPN off. Request the **Landslide Inventory** + **Landslide Susceptibility (NLSM)** for Chamoli. If it's still down after 2–3 days, ask the project guide or college GIS lab.
- [ ] When the data arrives: in QGIS, Export → Save Features As → GeoJSON, EPSG:4326 → `data/manual/gsi_landslides.geojson` and `data/manual/gsi_susceptibility.geojson`; re-run the script.
- [ ] (Optional) Free **OpenTopography** API key → `.env` (`OPENTOPO_API_KEY=`).
- [ ] (Optional) TomTom key, if live incidents are wanted.
- [x] ~~Install QGIS~~ (done)
- [x] ~~Look at the data in QGIS~~ (project saved at `qgis/safeyatra.qgz`)
- [x] ~~Accident list~~ (dropped)

### Agent / Claude (next; see §32 for the detailed plan)
- [ ] Proper slope raster + zonal statistics → better terrain_slope
- [ ] Routing prototype (notebook/script) with λ, on the demo routes
- [ ] FastAPI backend
- [ ] React + Leaflet frontend
- [ ] Optionally: add river and stream factors to the risk formula; percentile scaling
- [ ] Optionally: `git init` + first commit (only when the user asks)

---

## 28. How-to: common commands

```bash
# activate the environment
cd /home/aditya/gisproject
source .venv/bin/activate

# run the full data pipeline (uses the cache; ~30–90 s after the first run)
python scripts/fetch_chamoli_data.py

# re-download everything fresh
python scripts/fetch_chamoli_data.py --refresh

# run only some steps
python scripts/fetch_chamoli_data.py --only weather
python scripts/fetch_chamoli_data.py --only roads,elevation --segment-length 200

# use the Open-Meteo elevation API instead of tiles (slow, rate-limited)
python scripts/fetch_chamoli_data.py --elev-source open-meteo --max-elev-points 5000

# regenerate the app mockup images (after the data changes)
python scripts/make_mockups.py

# open QGIS
flatpak run org.qgis.qgis//lts
```

**Viewing data in QGIS:** New Empty Project → Browser → XYZ Tiles → OpenStreetMap → Home → gisproject → output → double-click the GeoJSON files → drag OpenStreetMap to the bottom → right-click boundary → Zoom to Layer → roads_segments → Properties → Symbology → **Categorized** by `risk_class` → Classify. Save in `qgis/`.

---

## 29. Progress log (what happened, in order)

All on **24 Nov 2026**.

1. Read `project_context.md`; summarised the deliverables (phases 0–9).
2. **venv created** with `virtualenv` (system `venv` broken: missing `python3.10-venv`); Python 3.10.12, pip upgraded.
3. User set the rule: **keep it college-level** (D1).
4. Tested the APIs: Nominatim ✅, Open-Meteo ✅, Overpass slow (overpass-api.de and mail.ru work), **NASA COOLR ArcGIS dead** → found the working **GLC CSV** fallback.
5. Created the project skeleton: `scripts/`, `data/manual/`, `data/raw/`, `cache/`, `output/`, `requirements.txt`, `.env.example`, `.gitignore`, `accidents.example.csv`.
6. Wrote **`fetch_chamoli_data.py`** (requests + stdlib) per spec §13.
7. First runs: fixed the CSV multiline parsing bug (`io.StringIO`); **Open-Meteo elevation hit 429** (600 points/min) → switched to **AWS Terrain Tiles** (+ Pillow) as the default, kept Open-Meteo as a paced fallback; widened the bbox sanity tolerance (80.102 vs 80.1).
8. Found imprecise NASA landslides (25–50 km) creating a false hotspot at Chamoli town → used only accuracy ≤ 10 km for risk (D8).
9. All §13.4 sanity checks pass (area 7,833 km², NH-7 continuous, elevations 767 / 3,125 m).
10. Explained the user's tasks; user asked why QGIS is needed (checking data visually, maps for the report, opening GSI shapefiles, slope).
11. **Installed QGIS** via Flatpak (user-level; first attempt needed a branch choice → LTS 3.28.9).
12. Wrote step-by-step QGIS instructions; the user saved `qgis/safeyatra.qgz`.
13. GSI Bhukosh checked: **times out** (also from this machine); gsi.gov.in works.
14. User **dropped the accident feature** (D4); created a headers-only `accidents.csv`.
15. Inventory of data had / lacking.
16. Added **rivers and streams** (Overpass) → `dist_to_river_m`, `stream_crossings`, `rivers.geojson`, rivers report in the summary.
17. **Web research** on Chamoli landslides (2021–2025) → 40 events, located via OSM stream crossings, villages and NH-7 snapping → `data/manual/web_landslides.csv`; loader added; landslides 41 → 78 (60 precise). Nandprayag is now the riskiest NH-7 stretch.
18. Explained the **app design** (data → FastAPI + A\* → React + Leaflet).
19. Built **`make_mockups.py`** and generated **11 mockup images** from real data and real A\* routes → `app images for future reference/`.
20. Wrote **this file**.
21. Added §0 (start here for a new agent), §32 (detailed next-steps plan) and §33 (gotchas) so another agent can take over.
22. Project moved to **Windows**; old Linux venv deleted, new Python 3.12 venv; QGIS 3.44.15 LTR installed with winget.
23. GSI still unavailable → added **NASA global susceptibility** fallback (weight 0.10) and a `places` step.
24. Built the **backend** (FastAPI, A\*, live risk from weather/GSI alert/closures/reports, Clerk JWT check, SQLite) and the **frontend** (React + DaisyUI + Leaflet + Clerk): Route, Report and Admin pages. Demo routes match §20 expectations (Karnaprayag→Gopeshwar 41.5 vs 39.8 km, 27% less high-risk road).

---

## 30. Reference links

**Data portals**
- GSI Bhukosh: https://bhukosh.gsi.gov.in
- GSI Bhusanket (forecast bulletins): http://www.bhusanket.gsi.gov.in/
- ISRO Landslide Atlas of India: https://www.isro.gov.in/Landslide_Atlas_India.html
- NASA Landslides: https://landslides.nasa.gov · https://gpm.nasa.gov/landslides/data.html
- NASA GLC export (dataset page): https://data.nasa.gov/dataset/global-landslide-catalog-export
- OpenTopography API: https://portal.opentopography.org/apidocs/
- AWS Terrain Tiles: https://registry.opendata.aws/terrain-tiles/
- Geofabrik India extracts: https://download.geofabrik.de/asia/india.html
- ISRO Bhuvan: https://bhuvan-app1.nrsc.gov.in/thematic/thematic/index.php

**APIs**
- Nominatim: https://nominatim.org/release-docs/latest/api/Search/ (policy: https://operations.osmfoundation.org/policies/nominatim/)
- Overpass: https://wiki.openstreetmap.org/wiki/Overpass_API
- Open-Meteo: https://open-meteo.com/en/docs · Elevation: https://open-meteo.com/en/docs/elevation-api · Archive: https://open-meteo.com/en/docs/historical-weather-api
- IMD API: https://api.imd.gov.in/public/api_reference.html
- TomTom Incidents: https://developer.tomtom.com/traffic-api/documentation/traffic-incidents/incident-details
- HERE Traffic v7: https://docs.here.com/traffic-api/

**Libraries**
- GeoPandas https://geopandas.org · Shapely https://shapely.readthedocs.io · Rasterio https://rasterio.readthedocs.io · rasterstats https://pythonhosted.org/rasterstats/ · NetworkX A\* https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.astar.astar_path.html · FastAPI https://fastapi.tiangolo.com · Leaflet https://leafletjs.com · React-Leaflet https://react-leaflet.js.org · QGIS https://qgis.org

**Key papers**
- Kirschbaum, Stanley & Zhou (2015), Geomorphology 249:4–15.
- Juang, Stanley & Kirschbaum (2019), PLOS ONE 14(7): e0218657.
- Shugar et al. (2021), *A massive rock and ice avalanche caused the 2021 disaster at Chamoli, Indian Himalaya*, Science, doi:10.1126/science.abh4455.

---

## 31. Glossary

| Term | Meaning |
|---|---|
| **A\*** | Shortest-path search that uses a heuristic (here, straight-line distance) to reach the goal faster than Dijkstra |
| **λ (lambda)** | Safety slider value: how strongly risk is penalised in the route cost |
| **Segment** | A ≤ 500 m piece of road between OSM nodes; the unit that gets a risk score |
| **u_node / v_node** | Start and end OSM node of a segment (graph vertices) |
| **static_risk** | Risk from permanent factors (landslides, slope, bends, susceptibility) |
| **risk_now / dynamic** | Risk adjusted for current weather / alerts (phase 2) |
| **Susceptibility (NLSM)** | GSI's National Landslide Susceptibility Mapping: zones rated Low → Very High |
| **Cross slope** | Steepness of the ground across the road (hillside), our terrain stand-in |
| **Curvature** | Total turning per km of road (°/km) |
| **Nala / gadhera** | Local words for a stream / mountain drain; debris flows come down these |
| **Toe erosion** | A river cutting the bottom of a slope, which makes it slide |
| **Overpass / Nominatim** | Free OSM query API / OSM geocoder |
| **Terrarium tiles** | PNG map tiles that store elevation in their RGB colours |
| **GLC / COOLR** | NASA Global Landslide Catalog / Cooperative Open Online Landslide Repository |
| **CRS / EPSG** | Coordinate reference system / its code (4326 = lat-lon, 32644 = UTM 44N metres) |
| **GeoJSON / GeoPackage / GeoTIFF** | Vector (web) / vector (QGIS database file) / raster file formats |
| **BRO / SDRF / NHIDCL** | Border Roads Organisation / State Disaster Response Force / the national highway building agency |

---

## 32. NEXT STEPS: detailed hand-off plan

This is the work queue, **in order**. Each step lists its goal, the files to create or change, the method, and **"done when"** checks. Steps marked 🔓 can start now; 🔒 needs something from the user first.

### Step 1 🔓 Proper terrain slope raster (replaces the `cross_slope_deg` stand-in)
- **Goal:** a real slope map (degrees) for Chamoli, plus per-segment slope statistics, as the spec intends (§13, spec §10.2).
- **Data:** reuse the **AWS Terrain Tiles** (zoom 12, ~33 m) already used by the pipeline. The `TerrainTiles` class in `fetch_chamoli_data.py` shows the URL and decoding. Only 80 tiles are cached (roads only); covering the whole district bbox needs about 12 × 13 ≈ 156 tiles (cheap, no limit). Alternative: the OpenTopography COP30 GeoTIFF, if the user adds `OPENTOPO_API_KEY`.
- **New dependencies (pip, in .venv):** `numpy`, `rasterio`, `rasterstats` (and `geopandas`, `shapely`, `pyproj` for Step 2). Wheels exist for Python 3.10; no sudo needed. Add them to `requirements.txt` (uncomment the phase-2 block).
- **Method:**
  1. New script `scripts/compute_slope.py`: mosaic the tiles over the boundary bbox into a numpy array (Web-Mercator pixel grid), write `output/dem_tiles_z12.tif` (EPSG:3857), then reproject to **EPSG:32644** with rasterio's `warp` → `output/dem_32644.tif`.
  2. Slope in degrees with numpy gradients (Horn method, or `np.gradient` with the 30 m pixel size): `slope = degrees(arctan(hypot(dz/dx, dz/dy)))` → `output/slope_32644.tif`.
  3. Per segment: buffer 50 m (in EPSG:32644) → `rasterstats.zonal_stats` mean and max → `terrain_slope_mean_deg`, `terrain_slope_max_deg`.
- **Then:** in the risk, use `terrain_slope = min(terrain_slope_mean_deg / 45, 1)` (keep the `cross_slope_deg` fallback if the raster is missing).
- **Done when:** the slope GeoTIFF opens in QGIS and looks right (steep valley walls, flat valley floors); every segment has `terrain_slope_mean_deg`; values are sensible (most 15–40°; Badrinath valley floor lower); risk re-computed; summary updated.

### Step 2 🔓 GeoPandas pipeline + GeoPackage deliverable (spec phase 2/4)
- **Goal:** the "final GIS datasets for teammates" deliverable: a clean **`output/road_segments.gpkg`** (+ CSV + GeoTIFFs).
- **Files (suggested, college-simple):**
  - `scripts/build_segments.py`: read `output/roads_segments.geojson` with GeoPandas, **clip roads to the district boundary**, reproject to EPSG:32644, add the slope zonal statistics from Step 1, recompute lengths in metres, and fix tiny gradient outliers (e.g., ignore the gradient for segments < 30 m, or cap at 40%).
  - `scripts/compute_risk.py`: the §13 risk formula in one place (weights at the top of the file), percentile scaling option (95th pct = 1.0), optional river factor, writes `static_risk`, `risk_class`, `risk_factors`.
  - `scripts/export_gpkg.py`: write the GeoPackage with layers `road_segments`, `landslides`, `rivers`, `pois`, `boundary`; plus `output/segments.csv`.
- **Keep `fetch_chamoli_data.py` as step 1** (it must keep working on its own). Don't rewrite it; build on its outputs.
- **Done when:** `road_segments.gpkg` opens in QGIS with all layers; the attributes match §12 (+ terrain_slope fields); the risk map looks plausible; the known hotspots (Nandprayag, Pagal Nala, Patalganga, Helang, Lambagad, Bhanerpani, Kameda) are high or very high.

### Step 3 🔓 Maps for the report (spec phase 3)
- **Goal:** map images: boundary, road network, elevation (DEM), slope, landslides (NASA vs news), rivers, risk map.
- **Option A (user, in QGIS):** give the user step-by-step instructions for a **Print Layout** (Project → New Print Layout → Add Map, Legend, Scale Bar, North Arrow, Title → Export as Image/PDF). They already have `qgis/safeyatra.qgz`.
- **Option B (agent):** a script `scripts/make_maps.py` with matplotlib/GeoPandas → `maps/*.png`. Include the attribution text.
- **Done when:** about 7 PNG/PDF maps with title, legend, scale bar, north arrow and attribution exist in a `maps/` folder.

### Step 4 🔓 Routing module + prototype (spec phase 5)
- **Goal:** risk-weighted A\* that the backend will import.
- **Files:** `backend/app/routing.py` (or `scripts/routing.py` first), plus optionally `notebooks/03_astar_prototype.ipynb` for the report.
- **Method:** load `roads_segments` (GeoJSON or GPKG) → `networkx.MultiDiGraph` (or Graph) with nodes `u_node`/`v_node` (coordinates from segment ends), edges with `length_m`, `travel_time_s`, `static_risk`, `risk_now`, `closed`, `geometry`. Weight function `length·(1 + λ·risk_now)`, ∞ if closed. Heuristic: haversine to the goal. Snap start/end to the nearest **main-road** node (trunk–tertiary). The working pure-Python version is `astar()` in `scripts/make_mockups.py`; port it to NetworkX `astar_path`.
- **Output:** the route dict described in §20 (GeoJSON line, km, minutes, risk avg/max, hazard stretches with km and reasons, comparison with λ = 0). The hazard stretch logic exists in `make_mockups.py` (`hazard_stretches()`, `reasons()`).
- **Tests (pytest):** λ = 0 equals the NetworkX shortest path by length; route risk doesn't increase as λ grows; closed edges are never used; h ≤ true cost on samples; the demo routes all resolve.
- **Known expected results:** Gopeshwar → Joshimath = one road (~59.2 km, same for all λ). Karnaprayag → Gopeshwar: λ = 0 → 39.8 km, λ = 10 → 41.5 km with ~27% less high-risk km.
- **Done when:** the tests pass and the demo routes (§3) print sensible results.

### Step 5 🔓 FastAPI backend (spec phase 6)
- **Structure (simple):**
  ```
  backend/
    app/main.py          ← FastAPI app, startup: load data + build graph
    app/routing.py       ← from Step 4
    app/risk.py          ← dynamic multiplier (rain_factor etc., §13)
    app/data.py          ← load GeoJSON/GPKG into memory
    app/updaters/weather.py ← hourly Open-Meteo refresh (APScheduler or a background loop)
    tests/
  ```
- **Endpoints:** §21 (`/health`, `/places`, `/route`, `/segments`, `/hazards`, `/weather`, `/pois`; reports/admin later). Return GeoJSON. Enable CORS for the frontend dev server.
- **Places list:** the 10 towns in §3 + POIs/villages from OSM (local JSON), with a Nominatim fallback (respecting the 1 request/s limit and the User-Agent rules).
- **Run:** `uvicorn app.main:app --reload` from `backend/`. Swagger docs at `/docs` (good for the demo).
- **Done when:** `/route?from=30.408,79.320&to=30.555,79.565&safety=5` returns both routes as GeoJSON in < 2 s; tests pass.

### Step 6 🔓 React + Leaflet frontend (spec phase 7)
- **Setup:** `npm create vite@latest frontend -- --template react` (Node 20 is installed), then `react-leaflet` + `leaflet`. Tailwind is optional; plain CSS is fine.
- **Match the mockups** in `app images for future reference/` (colours and layout in §17): left panel (search, slider, route cards, hazard list), map with risk-coloured roads, landslide triangles, legend, layer switches, segment popup.
- **Base map:** OSM tiles with "© OpenStreetMap contributors" (and Open-Meteo / NASA attribution in the footer).
- **Done when:** the user can pick From/To, move the slider, see both routes and the hazard list, and click roads for details. End-to-end demo works with the backend.

### Step 7 🔒/🔓 Live and phase-2 features
- Weather updater → `risk_now` (rain_factor per nearest town; §13) → the map recolours; rain banner.
- GSI forecast input (admin enters the district alert level).
- Reports + admin (SQLite or a JSON file is fine): POST /reports, verify/reject, closures (date-based). Verified blockages → `closed = True`.
- Nearest help along the route (POIs within 1.5 km; logic exists in `make_mockups.py` `s08_help`).
- **Done when:** a simulated heavy-rain scenario changes risks and routes; a verified report blocks a route.

### Step 8 🔒 When the user gets the GSI Bhukosh data
- The user (or agent) converts the shapefiles in QGIS → GeoJSON EPSG:4326 → `data/manual/gsi_landslides.geojson`, `data/manual/gsi_susceptibility.geojson`. (GeoPandas can also read the shapefiles directly: `gpd.read_file(...).to_crs(4326).to_file(...)`.)
- Check the susceptibility class field name (the loader auto-detects a key containing "susc" or "class"; values Low/Moderate/High/Very High or 1–4). Adjust `susc_value_to_class()` if GSI uses other labels.
- Re-run `fetch_chamoli_data.py`, then Step 2 scripts, then `make_mockups.py`. The susceptibility weight (0.30) will turn on automatically.
- **Done when:** summary shows `gsi` > 0 landslides; `landslide_susc_class` is filled for most segments; the risk map is updated.

### Step 9 🔓 Validation + report material (spec phase 9)
- Run the §24 checks: hold-out test (keep the 2024–25 news events back, check the share that falls on high-risk segments), hotspot check, sensitivity ±0.05 on the weights, routing tests.
- Produce tables and figures for the report; reuse the mockups and maps.
- Write a `README.md` for the repo (how to install and run), shorter than this file.

### Optional improvements (only if time allows or the user asks)
- Add a river/stream factor to the risk (e.g., `dist_to_river_m < 100` and `stream_crossings > 0`), and justify it in the report.
- Percentile-based normalisation.
- AHP-derived weights for the viva.
- Install the newer QGIS "stable" branch (`flatpak install --user flathub org.qgis.qgis//stable`).
- `git init` + `.gitignore` already present, **only when the user asks**.

### Keep this file updated
After finishing any step: update §14 (numbers), §18 (inventory), §23 (phase status), §27 (open tasks), §29 (progress log) and this section.

---

## 33. Gotchas and lessons learned

| # | Gotcha | What to do |
|---|---|---|
| G1 | `python3 -m venv` fails (no `ensurepip`; `python3.10-venv` missing, needs sudo) | Use `python3 -m virtualenv -p python3.10 .venv`, or just use the existing `.venv` |
| G2 | `fetch_chamoli_data.py` prints **JSON to stdout** and progress to **stderr** | Redirect: `python scripts/fetch_chamoli_data.py > run.json 2> run.log` |
| G3 | Overpass `overpass-api.de` often returns **502/504**; `kumi.systems` and `private.coffee` time out | The script falls back to `maps.mail.ru`. Queries take 20–60 s. Results are cached in `cache/` |
| G4 | NASA COOLR ArcGIS endpoints are **dead**; `data.nasa.gov/api/views/...` is 404 | Use the legacy CSV URL in §9; parse with `csv.DictReader(io.StringIO(text, newline=""))` (descriptions contain newlines) |
| G5 | **Open-Meteo elevation** counts each point as one call: 600/min, ~10k/day → HTTP 429 "Minutely API request limit exceeded" | Use the Terrain Tiles (default); if Open-Meteo is used, pace 100 points every 10 s |
| G6 | The NASA GLC has many records with 25–250 km location accuracy (pinned to town/district centres) | Don't use them for risk (D8); keep them for display only |
| G7 | Nominatim needs a User-Agent and ≤ 1 request/s; it can't find many small Uttarakhand places (Bhanerpani, Helang, Kameda, Chatwapipal, Patalganga, Kuntari…) | Use Overpass name regex with spelling variants; snap to NH-7 or stream crossings (see §16) |
| G8 | The OSM "Lambagad" hamlet point (30.6926, 79.5132) looks misplaced (next to Hanumanchatti) | Use the NH-7 × Khachar Gadhera crossing (30.64892, 79.52397) |
| G9 | Nandanagar = **Ghat** (old name) in OSM | Search "Ghat" (PHC Ghat 30.25715, 79.44804) |
| G10 | **GSI Bhukosh times out** (as of 24 Nov 2026), even from this machine | Only the user can retry (different network, no VPN) or ask their guide |
| G11 | Headless Chrome (`--headless=new`) screenshots are ~87 px short of `--window-size` | Render 200 px taller and crop with Pillow (done in `make_mockups.py`) |
| G12 | The QGIS Flathub **LTS branch is old (3.28.9)** and must be chosen explicitly (`org.qgis.qgis//lts`); a plain `flatpak install` asks to choose a branch and fails non-interactively | Use the full ref `app/org.qgis.qgis/x86_64/lts` (or `//stable` for the newest) |
| G13 | `make_mockups.py` **imports `fetch_chamoli_data`** (helpers + TOWNS) and reads `output/` | Run the pipeline first; keep the helper function names stable |
| G14 | The pipeline doesn't clip roads to the boundary (ways crossing it keep their full geometry) | Clip in Step 2 |
| G15 | Very short segments give huge gradients (up to 239%) | Ignore or cap in Step 2 |
| G16 | Mountain routes often have **no alternative** | Expected; present as risk-aware routing + warnings (§2) |
| G17 | Weather right now (late Nov) is 0 mm everywhere | To demo rain effects, use a simulated scenario (as in mockup 07) or the Open-Meteo **archive** API for a past monsoon date |
| G18 | Python is **3.10**: avoid 3.11+ only features (e.g., `tomllib`, `ExceptionGroup`, `typing.Self`) | |
| G19 | Paths with spaces: `app images for future reference/` | Quote paths in shell commands |
| G20 | `data/manual/accidents.csv` is intentionally header-only | Don't delete it (it keeps the loader from warning); don't add accident data (D4) |
