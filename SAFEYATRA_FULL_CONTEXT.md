# SafeYatra: Complete Project Context and Status

> **One file with everything about this project:** what it is, why it exists, the tech stack, data sources and APIs, every decision made so far, progress, what each file and folder does, and the plan ahead.
>
> **Last updated:** 24 Nov 2026 (night)
> **Project folder:** `C:\Users\Aditya\Desktop\gisproject` (Windows 11; the project started on Ubuntu at `/home/aditya/gisproject`)
> **Git repository:** https://github.com/Aditya-madwal/safeyatra (branch `main`)
> **Study area:** Chamoli district, Uttarakhand, India
> **Type:** Final-year college project (GIS + web app)
>
> The original hand-off spec is `project_context.md`; it was written before any work started. **This file supersedes it** wherever the two differ, because it records what was actually built and decided.

---

## 0. Start here (for a new agent picking up this project)

**Read in this order:** §0 (this) → §4 (decisions; must follow) → §10 (files) → §18 (data have/lack) → **§34 (QGIS and the NASA → GSI plan)** → **§32 (next steps; your work queue)** → §33 (gotchas). `README.md` has the run commands. Everything else is reference.

### Who the user is and how to work with them
- A **final-year college student** (GIS Developer role on a team project). Comfortable running commands when given them, but **not deeply technical**. They asked for explanations "in simple terms" and "start to end, clear to understand".
- When the user must do something by hand (websites, QGIS, forms), give **numbered step-by-step instructions** with the exact menu names and buttons. Use tables for summaries. Short sentences, no jargon (or explain it).
- **Keep everything at college level** (D1): simple, readable Python with comments; no heavy infrastructure. Prefer a few clear scripts over clever abstractions.
- The user likes being told **what's done, what's left, and what they need to do**, as short lists.
- They are happy for the agent to **do things itself** (e.g., they asked the agent to install QGIS and to research landslides on the web) rather than hand them back.
- **Do not** put the user's email or name into any external request (User-Agent etc.); use `CONTACT_EMAIL` from `.env` only if the user sets it (D5).
- The project is a **git repo** (remote above). Commit and push **only when the user asks**. Never commit `.env`; `.env.example` is the shared template.
- Recorded decisions (§4) are final. Don't reopen them (e.g., don't bring back the accident feature, D4).
- The user prefers leniency over perfection ("college project, no need to make it extremely accurate").

### Current state in one paragraph
**The app works end to end.** The data pipeline (`scripts/fetch_chamoli_data.py`) builds 5,820 risk-scored road segments for Chamoli. The **FastAPI backend** (`backend/`) loads them into a NetworkX graph and runs **risk-weighted A\*** routing. Risk updates live from hourly Open-Meteo rain, an admin-set GSI alert level, road closures, and user blockage reports. The **React frontend** (`frontend/`) uses **DaisyUI**, **Leaflet** and **Clerk** sign-in. It has three pages (Plan route, Report, Admin), light and dark themes, and a professional redesign. Clerk keys and the admin user id are set in `.env`. 16 backend tests pass. Code, data outputs and screenshots are pushed to GitHub. **The main open item is GSI Bhukosh data.** Landslide susceptibility currently comes from the **NASA global map** (coarser, lower weight); see §34. **QGIS is installed but not yet used** for processing.

### What changed on 24 Nov 2026 (evening and night)
- **Moved to Windows 11.** Python **3.12.3** venv in `.venv` (`.venv\Scripts\python.exe`), Node 22, QGIS **3.44.15 LTR** (installed with winget). The old Linux venv was deleted. Linux paths and commands further down are historical.
- **NASA global landslide susceptibility map** (`data/raw/nasa_susceptibility/`, ~1 km, 5 classes mapped to 1–4) stands in for the missing GSI data, at a **lower weight (0.10 instead of 0.30)**, because it rates almost all of Chamoli "very high". GSI files in `data/manual/` override it automatically. New segment field `susc_source` (`NASA` / `GSI`).
- New pipeline step `places` → `output/places.json` (1,068 towns and villages for search).
- **Backend and frontend built** (§7, §10, §21, §22). User-chosen stack: **auth = Clerk**, **UI = DaisyUI**, **frontend = React (JavaScript)**, backend = FastAPI. All keys live in the single root `.env`.
- **UI redesign:** neutral, professional look (Inter font, Lucide icons, muted slate-blue brand colour, light and dark themes, Esri gray base map), following the user's UI guidelines.
- **Git repo** created and pushed to GitHub, with app screenshots in `screenshots/` and the README.

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
34. [QGIS status, and why NASA data is used for now](#34-qgis-status-and-why-nasa-data-is-used-for-now)
35. [How to request GSI Bhukosh data (step by step)](#35-how-to-request-gsi-bhukosh-data-step-by-step)

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
| D2 | **Python 3** in a project venv (`.venv`). Now **Python 3.12.3 on Windows**; it was 3.10.12 on the old Ubuntu machine. | Matches the machine's default Python; the spec allows 3.10+ |
| D3 | **Phase 1 script uses only `requests` + the standard library** (+ **Pillow** to read elevation tiles). GeoPandas etc. come in phase 2. | Easy to run anywhere; matches the spec |
| D4 | **Accident feature DROPPED.** No `accidents.csv` data collection. The accident weight (0.15) is shared out among the other factors automatically; road bends and sharp turns act as the road-danger stand-in. The loader code stays, and `data/manual/accidents.csv` exists with headers only. | User decision: "let's not do this accident feature" |
| D5 | **The user's email is NOT put in the HTTP User-Agent.** The script reads an optional `CONTACT_EMAIL` from `.env`; the default User-Agent is `SafeYatra/0.1 (student project)`. | Privacy; the user never approved sharing it |
| D6 | **Default elevation source is AWS Terrain Tiles** (free, no key, ~30 m), not Open-Meteo. | Open-Meteo's free elevation API counts every point as one call (600/min, ~10k/day) and blocked us after ~600 points; 23k points are needed |
| D7 | **NASA landslides fall back to the Global Landslide Catalog CSV** because the COOLR ArcGIS endpoints in the spec are dead (404 / DNS failure). | Verified on 24 Nov 2026 |
| D8 | **Landslide records with poor location accuracy (25 km, 50 km, unknown) are kept in the GeoJSON but NOT used for risk.** Only accuracy ≤ 10 km (exact, 1km, 5km, 10km, gsi_inventory, stream-crossing, village-level, approximate) counts. | They were pinned to town or district centres and created a false hotspot at Chamoli town |
| D9 | **Rivers are attributes only for now** (`dist_to_river_m`, `stream_crossings`), not in the risk formula. | The spec's formula doesn't include them; adding them later is a one-line change |
| D10 | **The backend loads data files into memory** (GeoJSON/GeoPackage → NetworkX graph); PostGIS is optional, added only if the guide wants a database. | College-level simplicity (D1) |
| D11 | **QGIS 3.44.15 LTR on Windows** (installed with `winget install OSGeo.QGIS_LTR`). It was a Flatpak 3.28.9 LTS on Ubuntu. **Not used for processing yet** (§34). | Long-term-support version is the safe choice for a college project |
| D12 | **Google Maps is not a data source.** | Its APIs don't expose incidents; the terms forbid caching it or mixing it with our own routing; scraping breaks the terms |
| D13 | **NASA global susceptibility map replaces GSI until GSI data arrives**, at weight **0.10** (GSI keeps 0.30). GSI files in `data/manual/` take over automatically. | Bhukosh was unreachable and the user had no time to wait. NASA rates ~87% of roads "very high", so 0.30 turned most roads "high" (§34) |
| D14 | **Stack chosen by the user:** auth = **Clerk** (`@clerk/react` v6), UI = **DaisyUI 5** + Tailwind 4, frontend = **React (JavaScript, not TypeScript)**; backend left to the agent (**FastAPI**). | User instruction |
| D15 | **All keys and tokens go in the single root `.env`** (read by the backend, the frontend via Vite `envDir: '..'`, and the data scripts). `.env.example` is the committed template. | User instruction: "add it to .env, I will fill it later" |
| D16 | **Backend checks Clerk tokens with Clerk's public keys (JWKS)**, worked out from the publishable key, so the Clerk secret key is not needed. Admins = Clerk user ids in `ADMIN_USER_IDS`. | Simple and secure; no secret on the server |
| D17 | **UI follows the user's design guidelines**: neutral surfaces, no harsh colours outside the map, Inter font, Lucide icons (no emojis), light and dark themes, accessible components. | User instruction ("highly professional and classy") |
| D18 | **Demo rain scenarios** (Moderate / Heavy) can be switched on by an admin, because the weather is dry in November. Simulated values are always labelled "demo". | Lets the rain feature be shown in the viva |
| D19 | **`output/` is committed to Git** (so a fresh clone can run the app); `cache/`, `data/raw/`, `backend/storage/`, `.venv/`, `node_modules/` and `.env` are not. | The backend needs `output/`; everything ignored is regenerable or private |

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

### In use (24 Nov 2026)

| Layer | Tool | Notes |
|---|---|---|
| Language (data + backend) | **Python 3.12.3** | venv at `.venv` |
| Data pipeline | **requests**, **Pillow**, **rasterio**, **numpy** | API calls with caching; elevation tiles; NASA susceptibility GeoTIFF |
| Backend | **FastAPI** + **Uvicorn**, **python-multipart** | REST API, auto docs at `/docs`, photo uploads |
| Routing | **NetworkX** `astar_path` with a custom weight | Risk-weighted A\* (`backend/app/routing.py`) |
| Live weather | **httpx** + an asyncio background loop | Open-Meteo refreshed every 60 min |
| Auth (server) | **PyJWT** + **cryptography** | Verifies Clerk session tokens via JWKS |
| Storage | **SQLite** (Python built-in) | Reports, closures, admin settings (`backend/storage/safeyatra.db`) |
| Tests | **pytest** | 16 tests: routing rules + API |
| Frontend | **React 19** + **Vite 8** (JavaScript) | `frontend/` |
| UI | **DaisyUI 5** + **Tailwind CSS 4**, **lucide-react** icons, **Inter** font (@fontsource) | Custom light and dark themes in `frontend/src/index.css` |
| Map | **Leaflet** + **react-leaflet** | Canvas rendering for ~6,000 road pieces |
| Auth (client) | **Clerk** (`@clerk/react` v6) | Sign-in modal, user menu |
| Routing (pages) | **react-router-dom** | `/`, `/report`, `/admin` |
| Base maps | **Esri** light and dark gray canvas (default), OSM, OpenTopoMap | CARTO now needs a key, so Esri is used |
| Desktop GIS | **QGIS 3.44.15 LTR** | Installed; not used for processing yet (§34) |
| Mockup rendering | **Google Chrome (headless)** + HTML/SVG | `scripts/make_mockups.py` |
| Version control | **Git + GitHub** | https://github.com/Aditya-madwal/safeyatra |

### Planned but not used (by choice)

| Tool | Why not |
|---|---|
| GeoPandas, Shapely, PyProj, rasterstats | The pure-Python pipeline plus rasterio was enough; may still be used for the slope raster / GeoPackage (§32) |
| PostgreSQL + PostGIS | Files in memory + SQLite are enough (D10) |
| APScheduler | A simple asyncio loop does the hourly refresh |
| React Native / Flutter | The web app is responsive (bottom sheet on phones) |

---

## 8. Development environment setup

**Current machine (Windows 11):**

| Item | Detail |
|---|---|
| OS | Windows 11 Home |
| Python | **3.12.3** (default; `py -0` also lists 3.11 and 3.10). venv: `.venv` → `.venv\Scripts\python.exe` |
| Node.js / npm | **v22.19.0 / 11.2.0** |
| Git | 2.38.1 (identity `aditya-madwal`); repo pushed to GitHub |
| QGIS | **3.44.15 LTR** at `C:\Program Files\QGIS 3.44.15` (Start menu → "QGIS Desktop 3.44.15") |
| Chrome / Edge | Installed (headless Chrome used for mockups and screenshot checks) |
| Shells | PowerShell (main) and Git Bash |

Recreate the environments from scratch:
```powershell
cd C:\Users\Aditya\Desktop\gisproject
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm install
```

*History: the project started on Ubuntu 22.04 (Python 3.10.12 via `virtualenv`, QGIS Flatpak 3.28.9). That venv was Linux-only and was deleted when the project moved to Windows.*

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
| 7 | Landslides: GSI inventory + susceptibility (NLSM) | **GSI Bhukosh** `https://bhukosh.gsi.gov.in` (register → cart → emailed shapefiles) | Free, manual | ⏳ **Pending.** Access and files expected within days; steps in §35 | Will replace NASA: `data/manual/gsi_landslides.geojson`, `gsi_susceptibility.geojson` |
| 7b | Landslide susceptibility (stand-in) | **NASA Global Landslide Susceptibility Map** (Stanley & Kirschbaum 2017) `https://gpm.nasa.gov/sites/default/files/downloads/global-landslide-susceptibility-map-2-27-23.tif` (33 MB GeoTIFF, ~1 km, classes 1–5) | Free, no key | ✅ **In use** (weight 0.10) | `landslide_susc_class` for every segment until GSI arrives (§34) |
| 8 | GSI landslide forecast bulletins | `http://www.bhusanket.gsi.gov.in/` | Free, PDF/web, no API | ✅ Reachable (slow) | Phase 2, entered by hand |
| 9 | Weather | **Open-Meteo Forecast** `https://api.open-meteo.com/v1/forecast` (hourly precipitation, rain, snowfall, visibility, weather_code; `past_days=3`, `forecast_days=3`, `timezone=Asia/Kolkata`); all 10 towns in **one call** | Free, no key, non-commercial | ✅ | Rain past 72 h / next 24 h → rain factor |
| 10 | Elevation (default) | **AWS Terrain Tiles** (Terrarium PNG) `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`, zoom 12 (~33 m/pixel in Chamoli). Decoding: `elev = R*256 + G + B/256 − 32768` | Free, no key, no rate limit | ✅ (80 tiles cover all roads) | 23,075 elevation points |
| 10b | Elevation (fallback) | **Open-Meteo Elevation** `https://api.open-meteo.com/v1/elevation` (~90 m, 100 points per call) | Free; **600 points/min, ~10k/day** | ⚠️ Rate-limited | `--elev-source open-meteo`, paced at 100 points every 10 s |
| 11 | 30 m DEM GeoTIFF | **OpenTopography** `https://portal.opentopography.org/API/globaldem?demtype=COP30&...&API_Key=KEY` | Free key needed | ⏸ Not set up (no key) | For a proper slope raster in QGIS → `output/dem_cop30.tif` |
| 12 | Live incidents | TomTom Traffic Incidents v5 (bbox ≤ 10,000 km², so it's split into tiles) / HERE v7 | Free developer key | ⏸ Not set up (no key); coverage likely poor | Optional |
| 13 | Thematic layers | ISRO Bhuvan WMS `https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms` | Free | Not used yet | Display only |
| 14 | Google Maps | — | — | ❌ Not used (D12) | — |
| 15 | IMD API | `https://api.imd.gov.in` | Needs IP whitelisting | Not used (Open-Meteo first) | Possible upgrade later |
| 16 | Place names | Overpass (`place=town|village|hamlet|locality`) | Free | ✅ | 1,068 places → `output/places.json` (search box) |
| 17 | Base maps (app) | **Esri** World Light/Dark Gray Canvas `https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/...` · OSM tiles · OpenTopoMap | Free, attribution | ✅ | Map background. ❌ CARTO basemaps now need an API key |
| 18 | Sign-in | **Clerk** (instance `sharp-shrew-8589.clerk.accounts.dev`; JWKS at `/.well-known/jwks.json`) | Free dev tier; publishable key in `.env` | ✅ Configured | Sign-in, Report and Admin pages |

**Used live by the running app:** Open-Meteo (hourly), Clerk, and the map tile servers. Everything else is read from `output/`.

**Rate-limit etiquette built into the script:** response caching, retries with backoff, Overpass mirror fallback, ≥ 1.1 s between Nominatim calls, a polite User-Agent, and Open-Meteo pacing.

---

## 10. Folder and file guide

```
gisproject/
├── SAFEYATRA_FULL_CONTEXT.md        ← THIS FILE: complete context and status
├── README.md                        ← How to install and run, Clerk setup, screenshots (shown on GitHub)
├── YOUR_NEXT_STEPS.md               ← The user's own to-do list (website tasks, keys, QGIS maps)
├── project_context.md               ← Original hand-off spec (written before work began)
├── requirements.txt                 ← Python packages (pipeline + backend + tests)
├── .env                             ← Real keys (Clerk, admin ids...). NEVER committed
├── .env.example                     ← Committed template with blank values
├── .gitignore                       ← Ignores .env, .venv/, cache/, data/raw/, node_modules/, frontend/dist/, backend/storage/
├── .venv/                           ← Python 3.12 virtual environment (Windows). Not committed
│
├── scripts/
│   ├── fetch_chamoli_data.py        ← Data pipeline. Fetches everything, adds NASA/GSI susceptibility,
│   │                                   computes segment attributes and risk, writes output/. See §11
│   └── make_mockups.py              ← Renders the 11 mockup PNGs (uses google-chrome; written on Linux)
│
├── backend/                         ← FastAPI app (run from this folder)
│   ├── app/
│   │   ├── main.py                  ← API endpoints, app state, hourly weather loop, seeded sample closure
│   │   ├── routing.py               ← RoadGraph (NetworkX), A* with cost = length·(1 + λ·risk), hazard stretches, nearest help
│   │   ├── risk.py                  ← Live risk: rain, GSI alert, fog, report penalties, closures
│   │   ├── weather.py               ← Open-Meteo fetch, demo rain scenarios, alert messages
│   │   ├── store.py                 ← SQLite: reports, closures, settings
│   │   ├── auth.py                  ← Clerk JWT check (JWKS), admin check
│   │   ├── data.py                  ← Loads output/ into memory
│   │   └── config.py                ← Reads the root .env, paths, settings
│   ├── tests/                       ← pytest: test_routing.py, test_api.py (16 tests)
│   └── storage/                     ← Created at runtime: safeyatra.db + uploads/ (photos). Not committed
│
├── frontend/                        ← React + Vite + DaisyUI + Leaflet + Clerk (run `npm run dev` here)
│   ├── src/pages/                   ← MapPage (plan route), ReportPage, AdminPage
│   ├── src/components/              ← RiskMap, RouteResults, SegmentDetails, PlaceSearch, Legend,
│   │                                   Header, PageLayout, ui.jsx (design-system pieces: toasts, dialogs, tabs...)
│   ├── src/index.css                ← Design tokens: light/dark daisyUI themes, Leaflet restyling
│   ├── src/auth.jsx, api.js, useMapLayers.js, constants.js
│   └── vite.config.js               ← Proxies /api → 127.0.0.1:8000; reads .env from the project root
│
├── data/
│   ├── manual/                      ← Hand-made datasets the pipeline reads
│   │   ├── web_landslides.csv       ← 40 landslide events (2021–25) from web research (§16)
│   │   ├── accidents.csv            ← Headers only (D4)
│   │   ├── accidents.example.csv    ← Template (2 fake rows)
│   │   ├── (gsi_landslides.geojson)     ← TO ADD when GSI Bhukosh data arrives (EPSG:4326), see §35
│   │   └── (gsi_susceptibility.geojson) ← TO ADD when GSI Bhukosh data arrives (EPSG:4326), see §35
│   └── raw/                         ← Big downloads. Not committed
│       └── nasa_susceptibility/global_landslide_susceptibility_2017.tif ← NASA map (auto-downloaded if missing)
│
├── cache/                           ← ~26 MB of cached API responses. Not committed; use --refresh to re-download
│
├── output/                          ← ~18 MB, generated by the pipeline, COMMITTED (the backend needs it). See §12
│   ├── roads_segments.geojson       ← 5,820 segments with all attributes + risk (main deliverable)
│   ├── segments.csv, boundary.geojson, landslides.geojson, rivers.geojson, pois.geojson
│   ├── places.json                  ← 1,068 towns/villages for search
│   ├── weather.json, summary.json, accidents.geojson (empty)
│
├── qgis/safeyatra.qgz               ← QGIS project saved on the old Linux machine (layer paths may need relinking)
├── screenshots/                     ← App screenshots used in README.md
└── app images for future reference/ ← 11 early mockup PNGs + README.md (§17)
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
| Susceptibility | class 1→0.1, 2→0.4, 3→0.7, 4→1.0 | landslide_susc_class (**NASA now**, GSI later; source in `susc_source`) |
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
**Currently active:** susceptibility from **NASA at 0.10** (`NASA_SUSC_WEIGHT`; GSI would use 0.30), landslide_density 0.20, terrain_slope 0.20, curvature 0.15. The effective weights are 0.154 / 0.308 / 0.308 / 0.231.

NASA class mapping: NASA 1–2 (very low / low) → 1, 3 (moderate) → 2, 4 (high) → 3, 5 (very high) → 4. Each segment takes the highest class at its start, middle and end. In Chamoli: 5,038 segments are class 4, 748 class 3 and 34 class 2.

The same weights are repeated in `backend/app/risk.py` (keep them in sync).

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

gsi_alert_factor: none 0 / low 0.3 / moderate 0.6 / high 1.0.

**Implemented** in `backend/app/risk.py` → `update_live_risk()`, run at startup, after each hourly weather refresh and after every admin or report change:
`risk_now = min(landslide_part·(1 + rain + gsi) + other_part·(1 + fog) + report_penalty, 1)`. Here landslide_part is the share from susceptibility, past landslides and slope; other_part is bends. Fog = +0.2 when visibility < 200 m. Night factor is not implemented.

### Hard rules (implemented)
- Verified blockage → a closure is created for that segment → the router skips it.
- Admin closure between two points, with optional start/end dates → active only within the dates. A sample closure, Badrinath–Mana winter snow (15 Nov – 30 Apr), is seeded on first run.
- Unverified (pending) user report → risk += 0.3 on its segment for 6 h.

### Candidate additions
- River factor (e.g., `dist_to_river_m < 100` → +), stream crossings, GSI forecast. Each is a small change in `add_static_risk()`.

---

## 14. Current results (latest run)

Generated 24 Nov 2026 (re-run on Windows, ~20:33 IST, with NASA susceptibility and places).

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
| Risk (with NASA susceptibility at 0.10) | **low 55.6 km · medium 1,891.3 km · high 383.7 km · very high 0.9 km** (before NASA: low 511.8 · medium 1,746.9 · high 71.9 · very high 0.9) |
| Places | 1,068 (15 towns, 196 villages, 829 hamlets, 28 localities) |
| Riskiest NH-7 stretch | **Nandprayag** (risk 0.795 now; 0.76 before NASA). Matches news reports of repeated blockages |
| Demo routes (backend) | Karnaprayag → Gopeshwar: λ 0 = 39.8 km, λ 10 = 41.5 km with **27% less high-risk road**. Gopeshwar → Joshimath: one road, 59.2 km. Karnaprayag → Badrinath: 124.3 km. All routes return in < 0.5 s |
| Attribute distributions | cross_slope median 22° (95th pct 39°); curvature median 636°/km (95th 1,374); gradient median 5.3% (outliers up to 239% on very short segments); nearest hospital median 1.95 km |
| Remaining warnings | NASA COOLR offline (fallback used); GSI inventory and susceptibility files not found (NASA map used instead); OPENTOPO_API_KEY not set |

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

### ✅ Have (14)
1. District boundary
2. Road network (2,332 km, 5,820 segments)
3. Elevation for every segment (~30 m tiles)
4. Road gradient
5. Road bends + sharp turns
6. Hospitals / clinics / police / fuel (122) + distance to nearest hospital
7. Weather, live (10 towns, hourly in the app)
8. Rivers (61) + distance to river
9. Streams (807) + stream crossings
10. Past landslides: NASA (41, 2007–2017)
11. Past landslides: news (40 events, 2021–2025)
12. Risk score for every segment (static + live)
13. Place names for search (1,068)
14. Seasonal closures and GSI alert levels: entered by the admin in the app

### ⚠️ Have, but could be better (3)
15. **Landslide susceptibility**: from the **NASA global map** (~1 km, low weight). Fix: the GSI NLSM data (§34, §35).
16. **Terrain slope**: estimated from two points beside each segment. Fix: a proper slope raster + zonal statistics in a 50 m buffer (no key needed; could be done in QGIS).
17. **Landslide locations**: 15 news events are approximate, and news has reporting bias. Fix: the GSI inventory.

### ⏳ Waiting for GSI Bhukosh (2)
18. **GSI landslide susceptibility zones (NLSM)**: will replace NASA at the full 0.30 weight.
19. **GSI landslide inventory**: official landslide points.

### ❌ Optional (1)
20. Live incidents (TomTom, needs a key; coverage likely poor)

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
- **Implemented** in `backend/app/routing.py`: `RoadGraph` (NetworkX `MultiDiGraph`) + `nx.astar_path` with the weight function above and a haversine heuristic. Closed edges return `None` from the weight function, which hides them. Snapping uses the biggest connected network: main roads for route search, any road for admin closures and reports. Tests in `backend/tests/test_routing.py`.
- The earlier pure-Python prototype is still inside `scripts/make_mockups.py` (`astar()` with heapq).

---

## 21. Backend API design

**Implemented** in `backend/app/main.py`. All paths start with `/api`. Swagger docs: http://127.0.0.1:8000/docs.

| Method and path | Access | Purpose |
|---|---|---|
| GET /api/health | public | Status, segment count, whether sign-in is configured |
| GET /api/places?q=&limit= | public | Search the 1,068 local places (towns first) |
| GET /api/places/nearest?lat=&lon= | public | Name of the nearest place (labels map clicks) |
| GET /api/route?from=lat,lon&to=lat,lon&safety=λ | public | `{safe_route, shortest_route, comparison, weather_alerts, gsi_alert, simulated_weather, nearest_help}`. Each route has geometry, km, minutes, risk avg/max/class, high-risk km, km by class, hazard stretches, segment ids and an elevation/risk profile |
| GET /api/segments | public | Compact GeoJSON of all roads with current risk (cached, pre-gzipped) |
| GET /api/segments/{id} | public | Full attributes, factor breakdown with weights, reasons |
| GET /api/landslides, /api/rivers?kind=, /api/pois?category=, /api/boundary | public | Map layers |
| GET /api/weather | public | Per-town rain, alerts, scenario, GSI alert |
| GET /api/stats | public | Km by current risk class, closed km |
| GET /api/closures | public | Active closures |
| GET /api/reports/recent | public | Pending + verified reports for the map (no user ids) |
| GET /api/me | signed in | `{user_id, is_admin}` |
| POST /api/reports | signed in | Multipart form: type, lat, lon, description, optional photo (≤ 5 MB) |
| GET /api/reports/mine | signed in | The user's own reports |
| GET /api/admin/reports?status=, PATCH /api/admin/reports/{id} | admin | Review; verify → closure, reject → reopen |
| GET/POST /api/admin/closures, DELETE /api/admin/closures/{id} | admin | Closures between two points, with optional dates |
| GET/PUT /api/admin/settings | admin | `gsi_alert` (none/low/moderate/high), `rain_scenario` (live/moderate/heavy) |
| GET /api/uploads/{file} | public | Report photos |

Startup: load `output/` → refresh live risk → build the graph → seed the sample closure. A background loop fetches Open-Meteo every `WEATHER_REFRESH_MIN` minutes (default 60). Reports, closures and settings are stored in SQLite (`backend/storage/safeyatra.db`).

---

## 22. Frontend design

**Implemented** in `frontend/` (React + DaisyUI + Leaflet + Clerk). Screenshots are in `screenshots/` and the README.

- **Pages:**
  - **Plan route** (`/`). Supports shareable links like `/?from=Karnaprayag&to=Gopeshwar&safety=10`.
  - **Report** (`/report`, needs sign-in).
  - **Admin** (`/admin`, shown to signed-in users; the page checks admin rights and shows the user id to add to `ADMIN_USER_IDS`).
- **Layout:** white header (logo, nav, rain status, theme toggle, Clerk user menu). Side panel + map on desktop; on phones, a bottom sheet over a full-screen map.
- **Plan route panel:**
  - Linked A/B place inputs with keyboard suggestions, a pick-on-map button (Esc cancels) and a swap button.
  - **Segmented control** for the preference (Fastest/Balanced/Safe/Safest = λ 0/2/5/10), with a one-line explanation.
  - Results: a comparison **table** (distance, time, average risk, high-risk km), a summary line, and tabs for **Overview** (elevation + risk profile, km by class), **Hazards** (click to zoom) and **Help nearby** (emergency numbers 112/108/1070).
  - Before a search: suggested routes, district risk totals and a weather table.
- **Map:**
  - Esri gray base map (light or dark to match the theme), with Streets and Terrain options.
  - Layers: road risk (canvas), boundary, rivers, streams, past landslides, POIs, user reports.
  - Route in the brand colour, the shortest route dashed, hazard markers, a collapsible legend.
  - Clicking a road opens the **road details panel** (score, reasons, factor bars, details).
- **Design system** (D17):
  - Inter, Lucide icons, muted slate-blue `#2c4a6b`, neutral grays, light and dark daisyUI themes (`frontend/src/index.css`).
  - Reusable pieces in `components/ui.jsx`: Segmented, Tabs, Notice, EmptyState, Skeleton, ConfirmDialog, Toasts, ThemeToggle.
- **Accessibility:** risk is always shown as a dot plus a text label, visible focus rings, ARIA combobox and radios, native `<dialog>` for confirmations, reduced-motion support.

---

## 23. Implementation plan and phase status

| Phase | Deliverables | Owner | Status |
|---|---|---|---|
| **0. Setup** | venv, folders, requirements, .env.example, .gitignore, QGIS installed, git repo | All | ✅ Done (Windows; GitHub repo) |
| **1. Data collection** | `fetch_chamoli_data.py` end to end; summary passes the sanity checks | GIS | ✅ Done |
| 1+. Extra data | Rivers + streams; news landslide dataset; places; NASA susceptibility | GIS | ✅ Done |
| **2. Data preparation (QGIS / GeoPandas)** | Proper slope raster (EPSG:32644), zonal stats, clipped layers, `road_segments.gpkg` | GIS | ⬜ Not started (optional; a good QGIS task, §34) |
| **3. Maps** | Boundary, roads, elevation, slope, landslide, river, risk maps (QGIS layouts → PNG/PDF) | GIS | ⬜ Not started (QGIS project exists; no layouts yet) |
| **4. Risk attributes (final)** | Static risk with **GSI** susceptibility; validation | GIS | ⏳ Uses NASA for now; waiting for GSI (§34, §35) |
| **5. Routing** | Graph + A\* + λ; demo routes | Backend | ✅ Done (`backend/app/routing.py`, tests) |
| **6. API** | FastAPI endpoints + tests | Backend | ✅ Done (`backend/app/main.py`, 16 tests pass) |
| **7. Frontend** | Map + search + preference + results + risk layer | Frontend | ✅ Done and redesigned (`frontend/`) |
| **8. Live layers** | Weather updater, GSI alert input, reports + admin, closures | Backend + Frontend | ✅ Done (Clerk configured; admin user id set) |
| **9. Validation and report** | Metrics, screenshots, documentation, presentation | All | ⏳ Partly (screenshots + README done; validation metrics not yet) |
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

### Immediate next steps (summary; **full detail in §32**)
1. **User:** request GSI Bhukosh data (§35). Access and files are expected within days.
2. **When GSI arrives:** switch from NASA to GSI (§34 "How to switch"), re-run the pipeline, refresh the screenshots and numbers.
3. **Optional GIS work (good for the viva):** report maps in QGIS print layouts; slope raster; GeoPackage export.
4. **Validation for the report:** hotspot check, hold-out test, weight sensitivity (§24).

---

## 24. Validation and testing plan

- **Hold-out test:** keep back 20–30% of landslide points (e.g., the most recent years); check what % fall on or near high / very-high segments (success-rate / ROC per class).
- **Known hotspots check:** chronic NH-7 zones (Pagal Nala, Patalganga, Helang, Lambagad, Nandprayag, Bhanerpani, Kameda) should score high. **Currently Nandprayag scores very high (0.795 with NASA susceptibility).**
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
| Live blockages lack API coverage | No real-time closures | User reports + admin panel (built) |
| **Susceptibility from NASA's global map (~1 km)** | Coarse; rates ~87% of roads "very high", so it is given a low weight (0.10) | Replace with GSI NLSM data when it arrives (§34) |
| QGIS not yet used for processing | Weak "GIS workflow" story for the viva | Make report maps / slope raster in QGIS (§34) |
| Weather is dry in November | Live rain feature looks idle | Admin demo rain scenarios (D18) |

---

## 26. Licensing and attribution

- **OpenStreetMap** (roads, rivers, POIs, boundary): ODbL. Show "© OpenStreetMap contributors".
- **AWS Terrain Tiles** (Mapzen/Tilezen, SRTM-based in this region): attribute the terrain tile sources (Mapzen/Tilezen, SRTM/NASA).
- **Copernicus DEM** (if used): "© DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA".
- **Open-Meteo**: CC BY 4.0, non-commercial. "Weather data by Open-Meteo.com".
- **NASA Global Landslide Susceptibility Map**: cite Stanley, T. & Kirschbaum, D.B. (2017), *A heuristic approach to global landslide susceptibility mapping*, Natural Hazards 87, 145–164.
- **Esri base maps**: "Tiles © Esri, HERE, Garmin, © OpenStreetMap contributors" (shown on the map).
- **NASA Global Landslide Catalog**: cite Kirschbaum, D.B., Stanley, T., & Zhou, Y. (2015), *Spatial and temporal analysis of a global landslide catalog*, Geomorphology 249, 4–15; and Juang, Stanley & Kirschbaum (2019), COOLR, PLOS ONE 14(7): e0218657.
- **News sources**: cite each URL in the `source_url` column of `web_landslides.csv`.
- **Rishiganga disaster**: Shugar et al. (2021), *Science*, doi:10.1126/science.abh4455.
- **GSI Bhukosh** (when used): accept the terms; cite GSI.
- **ISRO Landslide Atlas / Bhuvan** (if used): cite NRSC/ISRO.
- **TomTom/HERE** (if used): follow their developer terms.

---

## 27. Open tasks (who does what)

### User
- [ ] **Request GSI Bhukosh data** (landslide susceptibility + inventory for Chamoli): steps in **§35**. Access and files are expected within days.
- [ ] When the files arrive: unzip them into `data/raw/gsi/` and tell the agent (or convert them yourself, §35 step 9).
- [ ] (Optional, recommended for the viva) Make the report maps in QGIS print layouts (`YOUR_NEXT_STEPS.md` task 5).
- [ ] (Optional) Free **OpenTopography** API key → `.env` (`OPENTOPO_API_KEY=`).
- [ ] (Optional) TomTom key, if live incidents are wanted.
- [x] ~~Install QGIS~~ (3.44.15 LTR on Windows)
- [x] ~~Clerk keys + admin user id in `.env`~~
- [x] ~~App screenshots~~ (`screenshots/`)
- [x] ~~Accident list~~ (dropped)

### Agent / Claude
- [x] ~~Routing (A\*), FastAPI backend, React frontend, live layers, UI redesign, git + GitHub~~
- [ ] When GSI arrives: switch NASA → GSI (§34), re-run the pipeline, check hotspots, update numbers in this file
- [ ] Optional: proper slope raster + zonal statistics; GeoPackage export; report maps by script
- [ ] Optional: validation metrics for the report (§24); river/stream factor; percentile scaling
- [ ] Commit and push only when the user asks

---

## 28. How-to: common commands

All commands are for **Windows PowerShell**, run from `C:\Users\Aditya\Desktop\gisproject`.

```powershell
# --- run the app (two terminals) ---
cd backend;  ..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000   # API + docs at :8000/docs
cd frontend; npm run dev                                                                # app at http://localhost:5173

# --- tests ---
cd backend; ..\.venv\Scripts\python.exe -m pytest -q

# --- data pipeline (uses the cache; ~45 s) ---
.\.venv\Scripts\python.exe scripts\fetch_chamoli_data.py > run.json 2> run.log
.\.venv\Scripts\python.exe scripts\fetch_chamoli_data.py --refresh          # re-download everything
.\.venv\Scripts\python.exe scripts\fetch_chamoli_data.py --only weather     # some steps only
# after re-running the pipeline, restart the backend so it reloads output/

# --- frontend build / lint ---
cd frontend; npm run build; npx oxlint

# --- git (only when the user asks) ---
git add -A; git commit -m "message"; git push
```
**Gotcha:** in PowerShell, `npm run dev -- --port 5173` loses the `--`. Use `npx vite --port 5173` instead.

Open QGIS from the Start menu: **QGIS Desktop 3.44.15**.

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
25. **Clerk configured:** publishable + secret key in `.env` (the secret key is not used), admin user id in `ADMIN_USER_IDS`.
26. **UI redesign** following the user's guidelines (D17): Inter, Lucide icons, neutral palette, light and dark themes, comparison table, tabs, bottom sheet on phones, confirm dialogs, toasts. CARTO base maps now need a key, so switched to Esri gray canvas.
27. **Git repo** initialised and pushed to https://github.com/Aditya-madwal/safeyatra (`.env` excluded, `output/` included). App screenshots added to `screenshots/` and the README.
28. Recorded **why QGIS isn't used yet and the NASA → GSI plan** (§34), plus GSI Bhukosh request steps (§35).

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

This is the work queue. Each step lists its goal, the files to create or change, the method, and **"done when"** checks. Steps marked 🔓 can start now; 🔒 needs something from the user first; ✅ is done.

**Status (24 Nov 2026, night):** Steps 4–7 ✅ done. Step 8 🔒 waits for GSI Bhukosh (highest priority once the files arrive; see §34). Steps 1–3 and 9 are open and optional; Steps 1 and 3 are good ways to give QGIS a real role.

### Step 1 🔓 Proper terrain slope raster (replaces the `cross_slope_deg` stand-in)
- **Goal:** a real slope map (degrees) for Chamoli, plus per-segment slope statistics, as the spec intends (§13, spec §10.2).
- **Data:** reuse the **AWS Terrain Tiles** (zoom 12, ~33 m) already used by the pipeline. The `TerrainTiles` class in `fetch_chamoli_data.py` shows the URL and decoding. Only 80 tiles are cached (roads only); covering the whole district bbox needs about 12 × 13 ≈ 156 tiles (cheap, no limit). Alternative: the OpenTopography COP30 GeoTIFF, if the user adds `OPENTOPO_API_KEY`.
- **New dependencies (pip, in .venv):** `numpy` and `rasterio` are already installed; add `rasterstats` (and `geopandas`, `shapely`, `pyproj` for Step 2). Add them to `requirements.txt`. **QGIS alternative:** Raster → Analysis → Slope, then Zonal Statistics on buffered roads.
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

### Step 4 ✅ Routing module (spec phase 5): DONE (`backend/app/routing.py`, `backend/tests/test_routing.py`). Original plan kept below for reference.
- **Goal:** risk-weighted A\* that the backend will import.
- **Files:** `backend/app/routing.py` (or `scripts/routing.py` first), plus optionally `notebooks/03_astar_prototype.ipynb` for the report.
- **Method:** load `roads_segments` (GeoJSON or GPKG) → `networkx.MultiDiGraph` (or Graph) with nodes `u_node`/`v_node` (coordinates from segment ends), edges with `length_m`, `travel_time_s`, `static_risk`, `risk_now`, `closed`, `geometry`. Weight function `length·(1 + λ·risk_now)`, ∞ if closed. Heuristic: haversine to the goal. Snap start/end to the nearest **main-road** node (trunk–tertiary). The working pure-Python version is `astar()` in `scripts/make_mockups.py`; port it to NetworkX `astar_path`.
- **Output:** the route dict described in §20 (GeoJSON line, km, minutes, risk avg/max, hazard stretches with km and reasons, comparison with λ = 0). The hazard stretch logic exists in `make_mockups.py` (`hazard_stretches()`, `reasons()`).
- **Tests (pytest):** λ = 0 equals the NetworkX shortest path by length; route risk doesn't increase as λ grows; closed edges are never used; h ≤ true cost on samples; the demo routes all resolve.
- **Known expected results:** Gopeshwar → Joshimath = one road (~59.2 km, same for all λ). Karnaprayag → Gopeshwar: λ = 0 → 39.8 km, λ = 10 → 41.5 km with ~27% less high-risk km.
- **Done when:** the tests pass and the demo routes (§3) print sensible results.

### Step 5 ✅ FastAPI backend (spec phase 6): DONE (see §21 for the real endpoints; weather lives in `app/weather.py`, not `app/updaters/`)
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

### Step 6 ✅ React + Leaflet frontend (spec phase 7): DONE with DaisyUI + Clerk and redesigned (§22)
- **Setup:** `npm create vite@latest frontend -- --template react` (Node 20 is installed), then `react-leaflet` + `leaflet`. Tailwind is optional; plain CSS is fine.
- **Match the mockups** in `app images for future reference/` (colours and layout in §17): left panel (search, slider, route cards, hazard list), map with risk-coloured roads, landslide triangles, legend, layer switches, segment popup.
- **Base map:** OSM tiles with "© OpenStreetMap contributors" (and Open-Meteo / NASA attribution in the footer).
- **Done when:** the user can pick From/To, move the slider, see both routes and the hazard list, and click roads for details. End-to-end demo works with the backend.

### Step 7 ✅ Live and phase-2 features: DONE (weather loop, demo rain, GSI alert, reports, closures, nearest help)
- Weather updater → `risk_now` (rain_factor per nearest town; §13) → the map recolours; rain banner.
- GSI forecast input (admin enters the district alert level).
- Reports + admin (SQLite or a JSON file is fine): POST /reports, verify/reject, closures (date-based). Verified blockages → `closed = True`.
- Nearest help along the route (POIs within 1.5 km; logic exists in `make_mockups.py` `s08_help`).
- **Done when:** a simulated heavy-rain scenario changes risks and routes; a verified report blocks a route.

### Step 8 🔒 When the user gets the GSI Bhukosh data (NEXT PRIORITY)
Follow **§34 → "How to switch from NASA to GSI"**. In short: convert the shapefiles to GeoJSON EPSG:4326 in `data/manual/`, check the class field and labels, re-run the pipeline (GSI replaces NASA automatically at weight 0.30), restart the backend, check the hotspots and spread, then update §14 / §18 / the screenshots.
- **Done when:** the summary shows `gsi` > 0 landslides; most segments have `susc_source = "GSI"`; the risk map has a sensible spread; the 16 tests still pass.

### Step 9 🔓 Validation + report material (spec phase 9)
- Run the §24 checks: hold-out test (keep the 2024–25 news events back, check the share that falls on high-risk segments), hotspot check, sensitivity ±0.05 on the weights, routing tests.
- Produce tables and figures for the report; reuse the screenshots, mockups and maps.
- ✅ `README.md` written (install, run, Clerk setup, screenshots).

### Optional improvements (only if time allows or the user asks)
- Add a river/stream factor to the risk (e.g., `dist_to_river_m < 100` and `stream_crossings > 0`), and justify it in the report.
- Percentile-based normalisation.
- AHP-derived weights for the viva.
- Serve the built frontend from FastAPI for a one-command demo.
- Commit and push changes to GitHub, **only when the user asks**.

### Keep this file updated
After finishing any step: update §14 (numbers), §18 (inventory), §23 (phase status), §27 (open tasks), §29 (progress log) and this section.

---

## 33. Gotchas and lessons learned

| # | Gotcha | What to do |
|---|---|---|
| G1 | *(Ubuntu only, historical)* `python3 -m venv` failed without `python3.10-venv` | On Windows, `py -3.12 -m venv .venv` works |
| G2 | `fetch_chamoli_data.py` prints **JSON to stdout** and progress to **stderr** | Redirect: `python scripts/fetch_chamoli_data.py > run.json 2> run.log` |
| G3 | Overpass `overpass-api.de` often returns **502/504**; `kumi.systems` and `private.coffee` time out | The script falls back to `maps.mail.ru`. Queries take 20–60 s. Results are cached in `cache/` |
| G4 | NASA COOLR ArcGIS endpoints are **dead**; `data.nasa.gov/api/views/...` is 404 | Use the legacy CSV URL in §9; parse with `csv.DictReader(io.StringIO(text, newline=""))` (descriptions contain newlines) |
| G5 | **Open-Meteo elevation** counts each point as one call: 600/min, ~10k/day → HTTP 429 "Minutely API request limit exceeded" | Use the Terrain Tiles (default); if Open-Meteo is used, pace 100 points every 10 s |
| G6 | The NASA GLC has many records with 25–250 km location accuracy (pinned to town/district centres) | Don't use them for risk (D8); keep them for display only |
| G7 | Nominatim needs a User-Agent and ≤ 1 request/s; it can't find many small Uttarakhand places (Bhanerpani, Helang, Kameda, Chatwapipal, Patalganga, Kuntari…) | Use Overpass name regex with spelling variants; snap to NH-7 or stream crossings (see §16) |
| G8 | The OSM "Lambagad" hamlet point (30.6926, 79.5132) looks misplaced (next to Hanumanchatti) | Use the NH-7 × Khachar Gadhera crossing (30.64892, 79.52397) |
| G9 | Nandanagar = **Ghat** (old name) in OSM | Search "Ghat" (PHC Ghat 30.25715, 79.44804) |
| G10 | **GSI Bhukosh** was timing out on 24 Nov 2026 | Only the user can request the data (§35). Try another network or browser, with VPN off. NASA is used meanwhile (§34) |
| G11 | Headless Chrome (`--headless=new`) screenshots are ~87 px short of `--window-size` | Render 200 px taller and crop with Pillow (done in `make_mockups.py`) |
| G12 | `qgis/safeyatra.qgz` was saved on Linux, so its layer paths point to `/home/aditya/...` | In QGIS: "Handle Unavailable Layers" → Auto-Find, or Browse to `output\` |
| G13 | `make_mockups.py` **imports `fetch_chamoli_data`** (helpers + TOWNS) and reads `output/` | Run the pipeline first; keep the helper function names stable |
| G14 | The pipeline doesn't clip roads to the boundary (ways crossing it keep their full geometry) | Clip in Step 2 |
| G15 | Very short segments give huge gradients (up to 239%) | Ignore or cap in Step 2 |
| G16 | Mountain routes often have **no alternative** | Expected; present as risk-aware routing + warnings (§2) |
| G17 | Weather right now (late Nov) is 0 mm everywhere | To demo rain effects, use a simulated scenario (as in mockup 07) or the Open-Meteo **archive** API for a past monsoon date |
| G18 | Python is now **3.12** on Windows | 3.11+ features are fine; keep code simple anyway |
| G19 | Paths with spaces: `app images for future reference/` | Quote paths in shell commands |
| G20 | `data/manual/accidents.csv` is intentionally header-only | Don't delete it (it keeps the loader from warning); don't add accident data (D4) |
| G21 | `npm create vite … --template react` sometimes scaffolds **vanilla TypeScript** | Use `npx create-vite@latest frontend --template react --no-interactive` and check `package.json` |
| G22 | PowerShell drops `--` in `npm run dev -- --port 5173`, so Vite treats `5173` as the root folder (every page returns 404) | Run `npx vite --port 5173` |
| G23 | `@clerk/clerk-react` is deprecated; **`@clerk/react` v6** uses `<Show when="signed-in">` instead of `SignedIn` / `SignedOut` | Use `@clerk/react`; check its exports before using old examples |
| G24 | Clerk shows keys as `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (Next.js naming) | This app is Vite: use **`VITE_CLERK_PUBLISHABLE_KEY`** |
| G25 | **CARTO base maps now return "API KEY REQUIRED"** tiles | Use Esri Canvas (World_Light/Dark_Gray_Base + _Reference), no key |
| G26 | Starlette `GZipMiddleware` recompressed the 2.8 MB `/api/segments` at level 9 on every request (~2 s) | The endpoint caches pre-gzipped bytes and sets `Content-Encoding`, so the middleware passes it through |
| G27 | The NASA susceptibility map rates ~87% of Chamoli roads "very high" | Don't give it the full 0.30 weight (`NASA_SUSC_WEIGHT = 0.10`) |
| G28 | Headless Chrome has a **minimum viewport of ~500 px** wide, so 390 px screenshots are cropped, not truly mobile | Don't judge the phone layout from them; check real devices / DevTools |
| G29 | `lucide-react` 1.x renamed icons (e.g. `CheckCircle2` → `CircleCheck`) | If the build fails on an icon import, look up the new name |
| G30 | `.env` holds the real Clerk keys and admin id | Never commit it; keep `.env.example` in sync with blank values |

---

## 34. QGIS status, and why NASA data is used for now

### Is QGIS used right now?
**No, not for processing.** QGIS 3.44.15 LTR is installed, and a project file (`qgis/safeyatra.qgz`) exists from the old Linux machine. All data work is done in Python (`scripts/fetch_chamoli_data.py`), and the app (backend + frontend) never uses QGIS.

### Why not?
QGIS's main job in this project was to **open and prepare the GSI Bhukosh data**: the official landslide susceptibility zones and the landslide inventory for Chamoli, delivered as shapefiles. That data **isn't available yet**:

- GSI Bhukosh (https://bhukosh.gsi.gov.in/) gives access and the files **after a request, which takes a few days** (steps in §35).
- The project couldn't wait, so it uses the **NASA Global Landslide Susceptibility Map** in the meantime. It downloads instantly, needs no login, and can be read directly in Python with rasterio, so QGIS isn't needed for it.

### NASA map vs GSI data

| | NASA global map (now) | GSI Bhukosh NLSM (later) |
|---|---|---|
| Coverage | Whole world | India (district-level detail) |
| Detail | ~1 km squares | Much finer (detailed maps) |
| Classes | 5 (very low … very high) → mapped to our 1–4 | Low / Moderate / High / Very High |
| How it rates Chamoli | ~87% of roads "very high", so it hardly separates roads | Should separate safer and riskier slopes much better |
| Weight in our risk score | **0.10** (low trust because it's coarse) | **0.30** (the full weight from the spec) |
| Landslide points | — (we use NASA catalogue + news: 78 points) | Official inventory (hundreds of events) |
| Status | ✅ In use | ⏳ Requested; files expected in days |

**Is NASA good enough?** For a working app and a college demo, yes. It is less precise, but the risk score also uses past landslides, hillside slope and road bends, which are detailed (~30 m). The routes and warnings make sense: Nandprayag is the riskiest NH-7 stretch, which matches news reports. **For the viva, say:** *"GSI's national data needs an access request, so we built the system with NASA's global susceptibility map (Stanley & Kirschbaum, 2017) at a lower weight. The design swaps in GSI data without code changes."*

### What happens when the GSI files arrive
The project is built so that GSI **automatically replaces NASA**. The pipeline uses GSI zones wherever they exist, and the NASA map is only loaded when no GSI file is present. **No changes are needed in the backend or frontend.**

**How to switch from NASA to GSI** (about an hour; the agent can do every step except downloading):
1. **User:** download the zip(s) from the GSI email and unzip them into `data/raw/gsi/`.
2. **Convert to GeoJSON in EPSG:4326**, in **QGIS** (§35 step 9) or Python (`gpd.read_file(...).to_crs(4326).to_file(...)`):
   - susceptibility polygons → `data/manual/gsi_susceptibility.geojson`
   - landslide inventory → `data/manual/gsi_landslides.geojson`
3. **Check the class field:** the loader looks for the first property containing "susc", otherwise "class", and understands Low / Moderate / High / Very High or 1–4. If GSI uses other labels or codes, update `susc_value_to_class()` in `scripts/fetch_chamoli_data.py`.
4. If the zones only cover part of the district, uncovered segments still fall back to NASA. Check `susc_source` counts (GSI vs NASA). If coverage is near-complete, consider dropping the fallback.
5. **Re-run the pipeline:** `.\.venv\Scripts\python.exe scripts\fetch_chamoli_data.py > run.json 2> run.log`. GSI segments get the full 0.30 weight automatically.
6. **Restart the backend** (it reloads `output/`), then run the tests: `cd backend; ..\.venv\Scripts\python.exe -m pytest -q`.
7. **Check the results:** risk spread by class (it should not be all one colour), hotspots (Nandprayag, Pagal Nala, Patalganga, Helang, Lambagad, Bhanerpani, Kameda should be high), and demo routes.
8. **Update the records:** §14, §18 and §34 status in this file, README screenshots if colours changed, report numbers. Commit and push if the user asks.

### Where QGIS fits from here
| Task | Why it helps |
|---|---|
| **Open and convert the GSI shapefiles** (when they arrive) | QGIS's main planned job; also shows a real GIS workflow |
| **Check the GSI zones against our roads visually** | Quality check before trusting the new weights |
| **Report maps** (print layouts: boundary, roads, slope, landslides, risk) | Needed for the report; shows QGIS use in the viva |
| *(Optional)* Slope raster (Raster → Analysis → Slope) + zonal statistics | Better terrain factor (§32 Step 1) |

---

## 35. How to request GSI Bhukosh data (step by step)

**What we need:** for **Chamoli district, Uttarakhand**:
1. **Landslide Susceptibility** map (NLSM, National Landslide Susceptibility Mapping)
2. **Landslide Inventory** (past landslide locations)

**Cost:** free. **Time:** about 30 minutes to request, then **a few days** for GSI to approve and email the files.

### Steps
1. **Open the website:** https://bhukosh.gsi.gov.in/ in Chrome or Edge.
   - If it doesn't load: turn off any VPN, try mobile data (phone hotspot) or college Wi-Fi, or try another browser.
2. **Create an account:** click **Register / Sign Up** (top right). Fill in your name, email, phone and organisation (your college).
   - **Purpose / remarks:** *"Academic final-year project: landslide risk-aware route planning for Chamoli district, Uttarakhand."*
3. **Confirm your email:** open the email from GSI and click the activation link. Check the spam folder too.
4. **Log in** to Bhukosh with your new account.
5. **Open the map viewer / data section** (look for **Map Viewer**, **Spatial Data**, **Data Download** or **Theme**).
6. **Find the landslide layers:** in the layer or theme list, open **Landslide** (sometimes under "Geohazards" or "Engineering Geology") and tick:
   - ☐ **Landslide Susceptibility** (may be called **NLSM**, 1:50,000)
   - ☐ **Landslide Inventory**
7. **Choose the area:** select **Uttarakhand → Chamoli**. If you can't choose a district, choose **Uttarakhand** (the agent will cut out Chamoli), or draw a box around Chamoli on the map.
8. **Add to cart and submit:** click **Add to Cart**, open the **Cart**, and **Submit / Checkout / Request**. Choose **Shapefile** if asked for a format. Note any request number.
9. **When the email arrives (a few days):** download the zip file(s), then either:
   - **Easy:** unzip into `gisproject\data\raw\gsi\` and tell the agent "GSI files are in data/raw/gsi". The agent converts them and switches the project over (§34).
   - **In QGIS (good viva practice):**
     1. Open QGIS → **Layer → Add Layer → Add Vector Layer** → choose the `.shp` file → **Add**.
     2. Right-click the layer → **Export → Save Features As…**
     3. Format **GeoJSON**, CRS **EPSG:4326 - WGS 84**, file name `gisproject\data\manual\gsi_susceptibility.geojson` (or `gsi_landslides.geojson` for the inventory) → **OK**.
     4. Tell the agent the files are in `data/manual/`.

> The website's menus may be named slightly differently from the steps above. Look for the words **Register**, **Landslide**, **Cart** and **Download**.

### If something goes wrong
| Problem | What to do |
|---|---|
| Website won't load | Different network or browser, VPN off; try again later in the day |
| No email after registering | Check spam; register again with another email |
| Can't find the landslide layers | Search the layer list for "landslide" or "NLSM"; look under Geohazards |
| No reply after about a week | Ask your project guide or the college GIS/geology lab (they often have GSI data); or contact GSI through the "Contact Us" page on gsi.gov.in |
| Request rejected | Re-apply and make the academic purpose clear (college name, project title, guide's name) |

**Until the files arrive, nothing is blocked.** The app runs fully on the NASA map (§34).
