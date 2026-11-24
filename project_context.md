# SafeYatra — Complete Project Context (A–Z)
 
> Hand-off document for continuing development in Claude Code.
> Last updated: 24 Nov 2026. Study area: **Chamoli district, Uttarakhand, India**.
 
---
 
## Table of contents
 
1. [Project summary](#1-project-summary)
2. [Problem statement & goals](#2-problem-statement--goals)
3. [Scope & study area](#3-scope--study-area)
4. [Team roles](#4-team-roles)
5. [Features](#5-features)
6. [Feasibility of each risk factor](#6-feasibility-of-each-risk-factor)
7. [Data sources (detailed)](#7-data-sources-detailed)
8. [Tech stack](#8-tech-stack)
9. [System architecture](#9-system-architecture)
10. [Risk model & parameters](#10-risk-model--parameters)
11. [Routing (A*) design](#11-routing-a-design)
12. [Data schemas](#12-data-schemas)
13. [Data-collection script specification](#13-data-collection-script-specification)
14. [Suggested repository structure](#14-suggested-repository-structure)
15. [API design (backend)](#15-api-design-backend)
16. [Frontend design](#16-frontend-design)
17. [Implementation phases](#17-implementation-phases)
18. [MVP definition](#18-mvp-definition)
19. [Validation & testing](#19-validation--testing)
20. [Known limitations, risks & decisions](#20-known-limitations-risks--decisions)
21. [Licensing & attribution](#21-licensing--attribution)
22. [Next steps](#22-next-steps)
23. [Reference links](#23-reference-links)
---
 
## 1. Project summary
 
**SafeYatra** is a GIS-based, hazard-aware route planner for the mountainous roads of Uttarakhand. Normal navigation apps find the *fastest* route. SafeYatra scores every road segment for **landslide risk** and **accident risk**. It uses an **A\* (A-Star)** search to recommend routes that balance distance/time against safety, and it warns travellers about dangerous stretches.
 
**Pitch line:** *Commercial maps tell you where a problem already is. SafeYatra tells you where problems are likely to happen.*
 
The first phase focuses on **Chamoli district**, which has the highest landslide frequency in Uttarakhand. It also contains the Rishikesh–Badrinath highway (NH-7), the Char Dham pilgrimage traffic, Joshimath, Gopeshwar, Karnaprayag and Govindghat.
 
---
 
## 2. Problem statement & goals
 
### Problem
- Mountain roads in Uttarakhand face frequent landslides (especially in the monsoon, Jun–Sep), sharp hairpin bends, steep drops and high accident rates.
- Travellers (tourists, pilgrims, locals) have no tool that shows **where** the risky stretches are or **how risky** a route is before they set out.
- Google Maps and similar apps react to incidents after they happen and don't model terrain or landslide risk.
### Goals
1. Collect, clean and analyse geographic data for Chamoli: roads, terrain, landslides, accidents and weather.
2. Compute a **risk score for every road segment**.
3. Provide **risk-aware routing** with A\*, using a user-controlled "safest ↔ fastest" balance.
4. Show warnings and safety information (risky stretches, rain alerts, nearest hospital).
5. Build a **user-friendly web platform** (mobile later).
6. Design it so it can extend to other Uttarakhand districts (Rudraprayag, Uttarkashi, Tehri, Pithoragarh…).
---
 
## 3. Scope & study area
 
| Item | Value |
|---|---|
| District | Chamoli, Uttarakhand |
| Area | ~7,700 km² (approx.) |
| Approx. bounding box (WGS84) | lon 78.9–80.1 E, lat 29.9–31.1 N (verify against the real boundary) |
| Working CRS (analysis) | **EPSG:32644** (WGS 84 / UTM zone 44N), in metres |
| Storage / web CRS | **EPSG:4326** (lat/lon) for GeoJSON and APIs |
| Key towns | Gopeshwar (HQ), Chamoli, Joshimath (Jyotirmath), Badrinath, Govindghat, Pipalkoti, Nandprayag, Karnaprayag, Tharali, Gairsain |
| Key roads | NH-7 (Rishikesh–Badrinath), Karnaprayag–Gwaldam–Tharali road, Gopeshwar–Ukhimath road (via Chopta), Karnaprayag–Gairsain road |
 
### Approximate town coordinates (verify before use)
| Town | Lat | Lon |
|---|---|---|
| Gopeshwar | 30.408 | 79.320 |
| Chamoli | 30.402 | 79.333 |
| Joshimath | 30.555 | 79.565 |
| Badrinath | 30.743 | 79.494 |
| Govindghat | 30.620 | 79.560 |
| Pipalkoti | 30.429 | 79.427 |
| Nandprayag | 30.333 | 79.317 |
| Karnaprayag | 30.263 | 79.217 |
| Tharali | 30.075 | 79.493 |
| Gairsain | 30.050 | 79.287 |
 
---
 
## 4. Team roles
 
| Role | Responsibilities |
|---|---|
| **GIS Developer** | Collect, prepare, analyse and manage geographic data: boundary, roads, DEM/slope, landslides, accidents. Compute road-segment risk attributes. Export GeoPackage / GeoTIFF / CSV / GeoJSON for teammates. Tools: QGIS, Python (GeoPandas). |
| Backend / Routing | Road graph, risk-weighted A\*, FastAPI service, PostGIS, live-data updaters. |
| Frontend | Web map UI (React + Leaflet/MapLibre), route search, risk visualisation, warnings, report-a-blockage. |
| Data / Validation (shared) | Accident dataset building, validation of risk scores, report and documentation. |
 
### GIS Developer's 6-step workflow (from the project brief)
1. **Collect geographic data**: Chamoli boundary, roads, elevation, landslide records, accident locations.
2. **Prepare data in QGIS**: clean datasets, clip to Chamoli, check CRS, fix geometry problems.
3. **Create maps**: district boundary, road network, elevation, slope, landslide and accident maps.
4. **Spatial analysis**: roads near landslide locations, accident-prone areas, overlapping hazard zones.
5. **Road risk attributes**: per-segment length, slope, hazard exposure, etc.
6. **Export final GIS datasets**: clean GeoPackage, GeoTIFF and CSV files for teammates.
---
 
## 5. Features
 
### Core (MVP)
- **Risk map of Chamoli roads**: every road segment colour-coded by risk (low / medium / high / very high).
- **Safe route search**: user picks a start and destination; the app returns the **safest** route and the **shortest** route side by side.
- **Safety slider (λ)**: from "fastest" to "safest", controlling how much risk is penalised.
- **Route risk breakdown**: total distance, estimated time, overall route risk score, and a list of high-risk stretches (with km markers and reasons such as "landslide zone", "steep slope", "sharp bends", "accident black spot").
- **Hazard layers toggle**: landslide points/zones, accident points, slope heatmap, district boundary.
### Phase 2 (live / dynamic)
- **Weather-aware risk**: rain forecast (next 24 h) and antecedent rain (past 72 h) increase landslide risk on affected segments.
- **GSI landslide forecast input**: when GSI issues a forecast bulletin for Chamoli, raise the risk of the affected areas.
- **Report a blockage**: users report landslides, accidents or closures with location + photo. Admins verify. Verified blockages remove the edge from routing.
- **Admin panel**: mark roads closed or open, approve reports, enter seasonal closures (e.g., snow closure beyond Joshimath/Badrinath in winter).
- **Live incidents (optional)**: TomTom/HERE incident APIs, if they have coverage in Chamoli.
### Phase 3 (nice to have)
- **Nearest help**: hospitals, PHCs, police stations, fuel pumps and SDRF posts along or near the route (from OSM).
- **Travel-time advice**: e.g., "avoid this stretch after dark", "heavy rain expected after 2 pm".
- **Offline mode / downloadable route** (patchy mobile network in the hills).
- **Mobile app** (React Native / Flutter).
- **Multi-district expansion**.
- **Multilingual UI** (Hindi / English / Garhwali labels).
---
 
## 6. Feasibility of each risk factor
 
| Factor | Feasible? | Source | Use in model |
|---|---|---|---|
| Landslides: historical inventory | ✅ Yes, strong | GSI Bhukosh (manual download), ISRO Landslide Atlas, NASA COOLR (API) | Static risk: count/density of past landslides near each segment, distance to nearest |
| Landslide susceptibility zones | ✅ Yes | GSI Bhukosh NLSM 1:50k (and 1:10k where available) | Static risk: susceptibility class of the zone each segment passes through |
| Landslide daily forecast | ✅ Yes (manual) | GSI Regional Landslide Forecasting System. Chamoli is in the bulletin districts (since the 2025 monsoon). No API: PDF/web bulletins | Dynamic multiplier during the monsoon |
| Slope / terrain | ✅ Easy | Copernicus GLO-30 / SRTM / ALOS / CartoDEM | Static risk: average/max slope, relief beside the road |
| Sharp bends / curvature | ✅ Easy | OSM road geometry | Static risk: curvature (°/km), count of hairpins |
| Weather: rain, snow, fog | ✅ Easy | Open-Meteo (free, no key, non-commercial); IMD API (needs IP whitelisting) | Dynamic multiplier |
| Accidents: historical | ⚠️ Partial, manual | MoRTH/Uttarakhand black-spot lists (PDFs), news reports, RTI / police request, iRAD/eDAR (not public) | Static risk: accident density per segment |
| Road blockages: live | ⚠️ Partial | User reports + admin panel; TomTom/HERE incidents (coverage likely thin) | Remove edge / heavy penalty |
| Accidents: live | ❌ Not realistically | No open feed | Not used. Use historical hotspots instead |
| Nearby help (hospitals, police, fuel) | ✅ Easy | OSM via Overpass | Info layer; optional small risk reduction |
| Seasonal closures | ⚠️ Manual | News, district notices | Date-based closure rules |
 
### Why Google Maps APIs are not the data source
- The Google Maps **app** shows accident and closure alerts, but **Google Maps Platform APIs do not expose an incident feed**.
- The Routes API gives only traffic speed bands along a route (`speedReadingIntervals`: NORMAL / SLOW / TRAFFIC_JAM), not the cause.
- Google's terms restrict caching data long-term and mixing Google routes/data into a non-Google map or graph, so we can't build a history or run our own A\* on their data.
- Scraping Google Maps (e.g., via SerpApi) breaks Google's terms. **Do not use.**
- Optional only: show "Google's fastest route" for comparison, on a Google map.
---
 
## 7. Data sources (detailed)
 
### 7.1 District boundary
| Option | Access | Notes |
|---|---|---|
| **OSM via Nominatim** | `https://nominatim.openstreetmap.org/search?q=Chamoli district, Uttarakhand, India&format=jsonv2&polygon_geojson=1&limit=5` | Pick the result with `osm_type=relation` and `class=boundary`. Returns the polygon + bbox. **Must send a `User-Agent` header; max 1 request/s.** |
| OSM via Overpass | See query in §13 | Overpass area id = `3600000000 + relation_id` |
| OSMnx | `ox.geocode_to_gdf("Chamoli, Uttarakhand, India")` | Easiest in Python |
| DataMeet / GADM / Survey of India | Manual download | Cross-check against official SoI boundary |
 
### 7.2 Road network
| Option | Access | Notes |
|---|---|---|
| **OSMnx** | `ox.graph_from_polygon(boundary, network_type="drive")` | Gives a routable NetworkX MultiDiGraph directly |
| **Overpass API** | POST to `https://overpass-api.de/api/interpreter` (mirrors: `https://overpass.kumi.systems/api/interpreter`, `https://overpass.private.coffee/api/interpreter`) | Raw OSM ways with tags + geometry |
| Geofabrik | `https://download.geofabrik.de/asia/india.html` (Uttarakhand / northern-zone extract) | .osm.pbf / shapefile, for offline processing |
 
Road classes for driving: `motorway, trunk, primary, secondary, tertiary, unclassified, residential, *_link` (optionally `service`, `track` for remote villages; flag these as low-quality).
 
Useful OSM tags: `highway, name, ref, surface, lanes, width, maxspeed, oneway, bridge, tunnel, smoothness`.
 
**Quality caveat:** NH-7 and main district roads are well mapped. Village link roads may be incomplete or missing.
 
### 7.3 Elevation (DEM) and slope
| Option | Access | Resolution | Notes |
|---|---|---|---|
| **Copernicus GLO-30** | OpenTopography Global DEM API: `https://portal.opentopography.org/API/globaldem?demtype=COP30&south=..&north=..&west=..&east=..&outputFormat=GTiff&API_Key=KEY` (free key) | 30 m | Best free option for the Himalaya |
| SRTM GL1 / ALOS AW3D30 | Same API (`demtype=SRTMGL1`, `AW3D30`), or USGS EarthExplorer | 30 m | Alternatives |
| **Open-Meteo Elevation API** | `https://api.open-meteo.com/v1/elevation?latitude=a,b,c&longitude=x,y,z` (up to 100 points per call, no key) | ~90 m (Copernicus GLO-90) | Quick point sampling along roads without downloading rasters |
| ISRO CartoDEM | Bhuvan / Bhoonidhi | 30 m | Indian source |
| Google Earth Engine | `COPERNICUS/DEM/GLO30` | 30 m | Fast for large areas |
 
Slope is computed in QGIS (`Raster → Analysis → Slope`) or with Rasterio/NumPy/RichDEM after reprojecting the DEM to EPSG:32644.
 
**Caveat:** a 30–90 m DEM gives terrain slope, not the road's own gradient. On hairpin roads the DEM cell includes the hillside. Use it as "terrain steepness around the road" (a landslide proxy), and compute road gradient from elevation difference over segment length as a secondary attribute.
 
### 7.4 Landslides
| Source | Access | Format | Notes |
|---|---|---|---|
| **GSI Bhukosh** (best Indian source) | `https://bhukosh.gsi.gov.in` → register → search by state/district → add Landslide Inventory + Landslide Susceptibility (NLSM) to the cart → accept terms → **data is emailed** | Shapefile | Free. Manual step; request early. GSI holds info on ~91,000 historical landslides nationally, with field-validated attributes |
| GSI Bhusanket portal / Bhooskhalan app | `http://www.bhusanket.gsi.gov.in/` | Web / app | Daily landslide forecast bulletins (Chamoli covered), inventory viewing |
| **ISRO/NRSC Landslide Atlas of India (2023)** | `https://www.isro.gov.in/Landslide_Atlas_India.html` | PDF + maps | ~80,000 landslides 1998–2022; seasonal, event-based and **route-wise** inventories (route-wise is very relevant) |
| **NASA COOLR / Global Landslide Catalog** | ArcGIS REST (below) or Landslide Viewer `https://landslides.nasa.gov` | GeoJSON/JSON via REST; .gdb/.shp/.csv download | Global; fewer points for Chamoli but has dates, fatalities and descriptions. Good for cross-checking |
 
**NASA COOLR ArcGIS REST endpoints** (discover layer ids via `?f=json` first; verify which host is live):
- `https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Reports_Points/MapServer`
- `https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Points/MapServer`
- `https://maps.nccs.nasa.gov/mapping/rest/services/COOLR/COOLR_Reports_Polygon/MapServer`
Query pattern:
```
{MapServer}/{layerId}/query?where=1%3D1
  &geometry={xmin},{ymin},{xmax},{ymax}
  &geometryType=esriGeometryEnvelope&inSR=4326
  &spatialRel=esriSpatialRelIntersects
  &outFields=*&outSR=4326&f=geojson
  &resultOffset=0&resultRecordCount=1000
```
Paginate while `exceededTransferLimit` is true. If `f=geojson` isn't supported, use `f=json` and convert Esri `{x, y}` geometry. Typical fields include `event_date`, `event_title`, `landslide_category`, `landslide_trigger`, `fatality_count`, `location_description`, `event_import_source` (GLC / LRC). Treat field names as "verify on first run".
 
Citation (required if published): Kirschbaum, D.B., Stanley, T., & Zhou, Y. (2015). *Spatial and temporal analysis of a global landslide catalog.* Geomorphology, 249, 4–15.
 
### 7.5 Accidents (hardest dataset)
No public API. Build the dataset in layers:
1. **Black-spot lists**: Uttarakhand Transport Dept road-safety cell (`https://transport.uk.gov.in/pages/view/70-roadsafetycell` → "Black Spots in Uttarakhand", Road Safety Year Books 2018–2022), MoRTH Lok Sabha / Rajya Sabha answers (state-wise NH black spots), Uttarakhand PWD documents. PDFs: extract place names → geocode manually in QGIS → points.
2. **News-based dataset**: collect reported Chamoli accidents (place, date, vehicle, deaths, injuries, source URL) and geocode. Mark `location_precision` (exact / approximate / village-level).
3. **Official request**: Chamoli District Police / SP Traffic, State Road Safety Cell, RTI for accident locations; IIT Madras CoERS (which analyses eDAR/iRAD) for academic collaboration.
4. **Proxy risk** when data is missing: curvature + gradient + drop-side exposure.
National context: eDAR (formerly iRAD) is MoRTH's national accident database, with all 36 States/UTs onboard since Nov 2022. Police capture GPS location and severity at the scene, but it is not publicly accessible.
 
**Manual CSV template** (`data/manual/accidents.csv`):
```csv
id,lat,lon,date,type,severity,fatalities,injuries,vehicle_type,description,location_precision,source,source_url
1,30.4290,79.4270,2025-07-12,accident,fatal,3,5,bus,"Bus fell into gorge near Pipalkoti",approximate,news,https://...
2,30.5550,79.5650,,black_spot,,,,,"Black spot listed by Transport Dept",approximate,transport_dept_pdf,https://...
```
`type` ∈ {accident, black_spot}; `severity` ∈ {fatal, grievous, minor, unknown}.
 
### 7.6 Weather
| Source | Access | Notes |
|---|---|---|
| **Open-Meteo Forecast** | `https://api.open-meteo.com/v1/forecast?latitude=..&longitude=..&hourly=precipitation,rain,snowfall,visibility,weather_code&daily=precipitation_sum,rain_sum,snowfall_sum&past_days=3&forecast_days=3&timezone=Asia/Kolkata` | Free for non-commercial use, **no API key**, CC BY 4.0. Hourly, up to 16 days. `past_days` gives antecedent rain |
| Open-Meteo Historical | `https://archive-api.open-meteo.com/v1/archive?...` | Back to 1940; use for correlating past landslides with rainfall |
| **IMD API** | `https://api.imd.gov.in/public/api_reference.html` (city forecast, current weather, district nowcast…) | Official, but **requires IP whitelisting** (form at `https://city.imd.gov.in/citywx/api_request.php`, then email). Treat as a later upgrade |
| NASA GPM IMERG | Earthdata | Satellite rainfall; research use |
 
Sample weather at the ~10 key towns (or on a 0.1° grid), then give each road segment the weather of its nearest sample point.
 
### 7.7 Live incidents (optional)
| Source | Access | Notes |
|---|---|---|
| **TomTom Traffic Incidents v5** | `https://api.tomtom.com/traffic/services/5/incidentDetails?key=KEY&bbox=minLon,minLat,maxLon,maxLat&fields={incidents{type,geometry{type,coordinates},properties{id,iconCategory,magnitudeOfDelay,events{description,code},startTime,endTime,from,to,length,delay,roadNumbers}}}&language=en-GB&timeValidityFilter=present` | Free dev tier. Categories include accident, jam, road works, road closed, flooding, dangerous conditions. **bbox max area is ~10,000 km²**, so split the Chamoli bbox into tiles |
| HERE Traffic API v7 | `https://data.traffic.hereapi.com/v7/incidents?in=bbox:...&apiKey=KEY` | Incident types include `roadClosure`, `accident`, `construction` |
| **Run one test query over Chamoli first.** If it returns almost nothing, rely on user reports + admin panel instead. | | |
 
### 7.8 Points of interest (help along the route)
Overpass query for `amenity=hospital|clinic|doctors|police|fuel`, `emergency=*`, `healthcare=*`, within the Chamoli area.
 
### 7.9 Thematic layers (optional)
- **ISRO Bhuvan** WMS/WMTS (OGC-compliant, usable directly in QGIS/OpenLayers): LULC 1:50k, geomorphology, lineaments, CartoDEM. WMS base: `https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms`. Mostly for display, not vector download.
- Geology / lithology / faults: GSI Bhukosh.
- Rivers / drainage (distance-to-river as a landslide factor): OSM `waterway=river|stream`.
---
 
## 8. Tech stack
 
| Layer | Choice | Why |
|---|---|---|
| Desktop GIS | **QGIS 3.x** | Cleaning, CRS fixes, slope, buffers, joins, map layouts |
| Data processing | **Python 3.11+**: `requests`, `geopandas`, `shapely` 2.x, `pyproj`, `rasterio`, `rasterstats`, `numpy`, `pandas`, **`osmnx`**, `networkx` | Standard open-source geospatial stack |
| Raster / terrain | `rasterio`, `richdem` (optional), GDAL CLI | Slope, aspect, curvature |
| Database | **PostgreSQL 16 + PostGIS 3** (+ **pgRouting** optional) | Spatial queries, production routing |
| Routing | MVP: **NetworkX `astar_path`** with a custom weight. Production: pgRouting `pgr_aStar`, or self-hosted GraphHopper / OpenRouteService with custom models / avoid-polygons | Start simple, scale later |
| Backend API | **FastAPI** (Python) + Uvicorn; Pydantic models | Same language as the GIS pipeline |
| Scheduler | APScheduler / cron / Celery beat | Hourly weather + incident refresh |
| Frontend | **React + Vite**, **Leaflet** (react-leaflet) or **MapLibre GL JS**, Tailwind CSS | Simple, free, OSM tiles |
| Base map tiles | OSM tiles (respect usage policy), OpenTopoMap (terrain look), or self-hosted vector tiles | Free |
| Geocoding (search box) | Nominatim (low volume) or Photon; or a local list of Chamoli places | Free |
| Mobile (later) | React Native or Flutter + MapLibre | |
| DevOps | Docker + docker-compose (postgis, api, web), GitHub, GitHub Actions | Reproducible setup |
| File formats | GeoPackage (.gpkg) for vectors, GeoTIFF for rasters, GeoJSON for web/API, CSV for tables | As required by the brief |
 
---
 
## 9. System architecture
 
```
┌──────────────────────── DATA SOURCES ────────────────────────┐
│ OSM (Nominatim/Overpass/OSMnx) · Copernicus DEM · GSI Bhukosh │
│ NASA COOLR · Accident CSV (manual) · Open-Meteo · GSI bulletin│
│ TomTom/HERE (optional) · User reports                         │
└───────────────────────────────┬───────────────────────────────┘
                                ▼
          ┌──────────── GIS PIPELINE (Python + QGIS) ────────────┐
          │ fetch → clean → clip to Chamoli → reproject 32644 →    │
          │ segment roads (~200–500 m) → attribute extraction →    │
          │ static risk score → export GPKG/GeoJSON/CSV/GeoTIFF    │
          └───────────────────────────┬───────────────────────────┘
                                      ▼
                         ┌──── PostGIS database ────┐
                         │ road_segments, landslides,│
                         │ accidents, pois, weather, │
                         │ reports, closures         │
                         └───────┬──────────┬────────┘
                 hourly ▲        │          │
   ┌──────── RISK UPDATER ───────┐│          │
   │ weather + GSI alert +       ├┘          ▼
   │ verified reports → dynamic  │   ┌──── ROUTING API (FastAPI) ────┐
   │ multiplier per segment      │   │ graph in memory (NetworkX)     │
   └─────────────────────────────┘   │ A* with risk-weighted cost     │
                                     │ /route /segments /hazards …    │
                                     └───────────────┬────────────────┘
                                                     ▼
                                   ┌──── WEB APP (React + Leaflet) ────┐
                                   │ search · safety slider · route    │
                                   │ risk colours · warnings · reports │
                                   └───────────────────────────────────┘
```
 
---
 
## 10. Risk model & parameters
 
### 10.1 Road segmentation
- Split OSM ways into segments of **~200–500 m** (default 500 m for v1; 200 m for finer analysis).
- Each segment keeps the parent `osm_way_id`, `highway` class, `name`, `ref`.
- In the graph, each segment = an edge (or keep OSMnx edges and attach aggregated attributes).
### 10.2 Per-segment attributes (GIS developer output)
| Attribute | Unit | How computed | Source |
|---|---|---|---|
| `length_m` | m | Geometry length in EPSG:32644 | OSM |
| `highway` | class | OSM tag | OSM |
| `surface`, `lanes`, `width` | — | OSM tags (often missing) | OSM |
| `elev_start_m`, `elev_end_m`, `elev_min_m`, `elev_max_m` | m | Sample DEM at vertices | DEM |
| `gradient_avg_pct` | % | \|Δelev\| / length × 100 | DEM |
| `gradient_max_pct` | % | Max between consecutive samples | DEM |
| `terrain_slope_mean_deg`, `terrain_slope_max_deg` | ° | Zonal stats of the slope raster within a 50 m road buffer | DEM |
| `downslope_drop_m` | m | (optional) Max elevation drop within 100 m perpendicular to the road | DEM |
| `curvature_deg_per_km` | °/km | Sum of \|heading change\| / length | OSM geometry |
| `sharp_turns` | count | Heading changes > 60° (vertices ≥ 10 m apart) | OSM geometry |
| `landslide_susc_class` | 1–4 | Susceptibility zone at the segment (max or length-weighted) | GSI NLSM |
| `landslides_within_500m` | count | Inventory points/polygons within a 500 m buffer | GSI + NASA |
| `nearest_landslide_m` | m | Distance to nearest landslide | GSI + NASA |
| `accidents_within_500m` | count | Accident points within 500 m (weighted: fatal 3, grievous 2, minor 1) | Accident CSV |
| `is_black_spot` | bool | Black-spot point within 250 m | Accident CSV |
| `dist_to_river_m` | m | Distance to nearest river (toe erosion) | OSM |
| `nearest_hospital_m` | m | Distance to nearest hospital/clinic | OSM |
| `nearest_weather_point` | id | Nearest weather sample town | — |
| `static_risk` | 0–1 | Formula below | computed |
| `risk_class` | low/med/high/very_high | Thresholds below | computed |
 
### 10.3 Normalisation (min–max or capped)
Each factor is scaled to 0–1 before weighting:
| Factor | Normalisation (v1 suggestion) |
|---|---|
| Susceptibility | class 1→0.1, 2→0.4, 3→0.7, 4→1.0 (Low/Moderate/High/Very High) |
| Landslide density | `min(landslides_within_500m / 5, 1)` |
| Terrain slope | `min(terrain_slope_mean_deg / 45, 1)` |
| Curvature | `min(curvature_deg_per_km / 1500, 1)` (calibrate on data percentiles) |
| Accident density | `min(weighted_accidents_within_500m / 5, 1)`; `is_black_spot` → at least 0.8 |
| Gradient | `min(gradient_avg_pct / 12, 1)` |
 
Prefer **percentile-based scaling** (e.g., 95th percentile = 1.0) once real data is in, so outliers don't flatten everything.
 
### 10.4 Static risk formula (v1 weights; justify or tune in the report)
```
static_risk = 0.30 · susceptibility
            + 0.20 · landslide_density
            + 0.20 · terrain_slope
            + 0.15 · curvature
            + 0.15 · accident_density
```
- If susceptibility data is not yet available, redistribute its weight proportionally among the rest.
- Alternative (for the report): weights via **AHP (Analytic Hierarchy Process)**, or a trained model (logistic regression / random forest on landslide presence) in later versions.
**Risk classes:** `low < 0.25 ≤ medium < 0.5 ≤ high < 0.75 ≤ very_high`.
 
### 10.5 Dynamic multiplier (updated hourly)
```
dynamic = 1
        + rain_factor          # 0 … 1.0
        + gsi_alert_factor     # 0 / 0.3 / 0.6 / 1.0 for none/low/moderate/high bulletin
        + night_factor         # optional 0.1–0.2 between sunset and sunrise
        + fog_snow_factor      # optional, from weather_code / visibility / snowfall
```
Suggested `rain_factor` (applies mainly to the landslide components):
| Condition (nearest weather point) | rain_factor |
|---|---|
| next-24h rain < 10 mm and past-72h < 30 mm | 0 |
| next-24h 10–35 mm or past-72h 30–75 mm | 0.3 |
| next-24h 35–65 mm or past-72h 75–150 mm | 0.6 |
| next-24h > 65 mm or past-72h > 150 mm | 1.0 |
 
(Thresholds loosely follow IMD's rain categories: moderate 15.6–64.4 mm/day, heavy 64.5–115.5, very heavy 115.6–204.4. Calibrate later against historical landslide dates using the Open-Meteo archive.)
 
A more precise variant applies weather only to the landslide part:
```
risk_now = landslide_part · (1 + rain_factor + gsi_alert_factor)
         + accident_part  · (1 + night_factor + fog_snow_factor)
```
 
### 10.6 Hard rules
- **Verified blockage / closure** → edge removed from the graph (or cost = ∞).
- **Seasonal closure** (date-based) → edge removed in that date range.
- Unverified user report → temporary penalty (e.g., risk += 0.3, expires after 6 h unless confirmed).
---
 
## 11. Routing (A*) design
 
### Graph
- Build from OSMnx (`network_type="drive"`), or from segmented roads (nodes at segment ends/intersections).
- Keep it **directed**; respect `oneway` (rare in Chamoli).
- Node attributes: `x` (lon), `y` (lat). Edge attributes: `length_m`, `travel_time_s`, `static_risk`, `dynamic`, `risk_now`, `closed`.
### Travel time
`travel_time_s = length_m / speed_mps`. Default speeds for hills if `maxspeed` is missing: trunk 35 km/h, primary 30, secondary 25, tertiary 20, unclassified/residential 15, track 10.
 
### Edge cost
```
cost(e) = length_m(e) · (1 + λ · risk_now(e))       if not closed
cost(e) = ∞                                          if closed
```
- **λ (safety slider):** 0 = pure shortest; suggested UI range 0–10 (e.g., 0, 2, 5, 10 presets: Fastest / Balanced / Safe / Safest).
- Variant: use `travel_time_s` instead of `length_m` as the base.
### Heuristic
`h(n) = haversine(n, goal)` in metres (or straight-line time at max speed when using time as the base). Since `cost(e) ≥ length_m(e) ≥ straight-line distance`, the heuristic is **admissible** → A\* returns the optimal path for the given λ. (Good viva point.)
 
### Output per route
- Geometry (GeoJSON LineString), `distance_km`, `est_time_min`
- `route_risk_avg` (length-weighted mean of `risk_now`), `route_risk_max`
- `hazard_stretches[]`: consecutive segments with `risk_class ≥ high`, with start/end km, length and reasons
- Comparison with the λ = 0 route: `extra_km`, `risk_reduction_pct`
### Reality check (important)
Mountain districts often have **only one road** between towns. The safest route may equal the shortest. The product must still be useful: show the risk along the only route, warn, suggest timing, and show the nearest help. Present the project as **"risk-aware routing + warnings"**, not just "alternative routes".
 
---
 
## 12. Data schemas
 
### 12.1 `road_segments` (GeoPackage layer / PostGIS table)
```
segment_id            TEXT PK          -- e.g. "w123456_s003"
osm_way_id            BIGINT
u_node, v_node        BIGINT           -- graph endpoints
highway               TEXT
name, ref             TEXT
surface, lanes, width TEXT
length_m              REAL
elev_start_m, elev_end_m, elev_min_m, elev_max_m REAL
gradient_avg_pct, gradient_max_pct REAL
terrain_slope_mean_deg, terrain_slope_max_deg   REAL
curvature_deg_per_km  REAL
sharp_turns           INT
landslide_susc_class  INT              -- 1..4, NULL if unknown
landslides_within_500m INT
nearest_landslide_m   REAL
accidents_within_500m REAL             -- severity-weighted
is_black_spot         BOOLEAN
dist_to_river_m       REAL
nearest_hospital_m    REAL
nearest_weather_point TEXT
static_risk           REAL             -- 0..1
risk_class            TEXT
dynamic               REAL DEFAULT 1   -- updated hourly
risk_now              REAL
closed                BOOLEAN DEFAULT false
geom                  LINESTRING, SRID 4326 (store 32644 copy if needed)
```
 
### 12.2 `landslides`
```
id, source (GSI|NASA_GLC|NASA_LRC|ISRO|news), event_date, category, trigger,
fatalities, description, location_precision, geom (POINT/POLYGON 4326)
```
 
### 12.3 `accidents`
Same columns as the CSV template in §7.5, + `geom POINT 4326`.
 
### 12.4 `pois`
```
id, osm_id, category (hospital|clinic|police|fuel|sdrf|...), name, phone, geom POINT
```
 
### 12.5 `weather_points`
```
point_id, name, lat, lon, fetched_at, rain_past_72h_mm, rain_next_24h_mm,
snow_next_24h_cm, min_visibility_m, weather_code_now, rain_factor
```
 
### 12.6 `reports` (user-submitted)
```
id, type (landslide|accident|closure|other), description, photo_url, geom POINT,
reported_at, status (pending|verified|rejected|expired), verified_by, expires_at
```
 
### 12.7 `closures`
```
id, segment_ids[], reason, start_date, end_date, recurring_yearly BOOL, source
```
 
---
 
## 13. Data-collection script specification
 
**Goal of step 1:** one Python script (`scripts/fetch_chamoli_data.py`) that pulls every dataset available through APIs, loads the manual datasets if present, and **prints a JSON summary** (also writing full JSON/GeoJSON to `output/`). Once the data looks right, move on to the user-friendly product.
 
> Status: started but not finished in the previous session. It has not been run against the live APIs yet. Build and run it in Claude Code.
 
### 13.1 Requirements
- Python 3.10+. Phase-1 core needs only `requests` (+ stdlib). Optional: `geopandas`, `shapely`, `osmnx`, `rasterio` for the QGIS-grade pipeline.
- Send `User-Agent: SafeYatra/0.1 (student project; contact: <email>)` on all requests (Nominatim requires it).
- **Cache** raw responses in `cache/` (hash of URL+params) and add a `--refresh` flag.
- Retries with backoff; fallback Overpass mirrors; polite delays (Nominatim ≥ 1 s).
- Optional keys via env vars: `TOMTOM_API_KEY`, `OPENTOPO_API_KEY`, `HERE_API_KEY`.
### 13.2 CLI
```
python scripts/fetch_chamoli_data.py
  [--only boundary,roads,pois,landslides,weather,elevation,incidents,dem,manual]
  [--segment-length 500]
  [--road-classes main|all]      # main = trunk..tertiary(+links); all = + unclassified, residential
  [--max-elev-points 5000]
  [--full]                       # print full JSON instead of summary
  [--refresh]                    # ignore cache
  [--out output/]
```
 
### 13.3 Steps
1. **Boundary**: Nominatim search → relation id + polygon + bbox. Fallback: Overpass
```
[out:json][timeout:180];
area["name"="Uttarakhand"]["admin_level"="4"]->.st;
rel(area.st)["boundary"="administrative"]["admin_level"="5"]["name"~"Chamoli"];
out geom;
```
   Overpass area id = `3600000000 + relation_id`.
2. **Roads**: Overpass
```
[out:json][timeout:300];
area(id:AREA_ID)->.a;
way(area.a)["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential)(_link)?$"];
out tags geom;
```
   → list of ways `{osm_id, highway, name, ref, surface, lanes, width, coords[[lon,lat]...]}`.
3. **POIs**: Overpass
```
[out:json][timeout:180];
area(id:AREA_ID)->.a;
( nwr(area.a)["amenity"~"^(hospital|clinic|doctors|police|fuel)$"];
  nwr(area.a)["healthcare"];
  nwr(area.a)["emergency"="ambulance_station"]; );
out center tags;
```
4. **Landslides (NASA COOLR)**: discover layers from each MapServer (`?f=json`), query each point layer with the district bbox, paginate, then filter points to inside the district polygon (ray-casting point-in-polygon; handle MultiPolygon and holes).
5. **Manual data loaders** (skip with a warning if missing):
   - `data/manual/gsi_landslides.geojson` (Bhukosh inventory exported from QGIS to EPSG:4326; use polygon centroids)
   - `data/manual/gsi_susceptibility.geojson` (field auto-detect: first key containing `susc` or `class`)
   - `data/manual/accidents.csv` (template in §7.5)
6. **Weather**: Open-Meteo forecast for the 10 key towns (hourly `precipitation, rain, snowfall, visibility, weather_code`; daily `precipitation_sum`; `past_days=3`, `forecast_days=3`, `timezone=Asia/Kolkata`) → `rain_past_72h_mm`, `rain_next_24h_mm`, `snow_next_24h_cm`, `min_visibility_m`, `rain_factor`.
7. **Segmentation**: split each way into ≤ `segment_length` pieces (cut at vertices; haversine distances).
8. **Elevation**: Open-Meteo elevation API for start/mid/end of each segment (dedupe points rounded to 4 decimals; 100 points per call; cap with `--max-elev-points`, prioritising main roads) → elevations + `gradient_avg_pct`, `gradient_max_pct`.
9. **Geometry attributes**: `curvature_deg_per_km`, `sharp_turns`.
10. **Proximity attributes**: `landslides_within_500m`, `nearest_landslide_m`, `accidents_within_500m` (weighted), `is_black_spot`, `nearest_hospital_m`, `nearest_weather_point` (pure Python is OK for v1. Use an equirectangular approximation + a bbox prefilter or simple grid index for speed. Switch to GeoPandas `sjoin_nearest` later).
11. **Preliminary `static_risk` + `risk_class`** with the §10.4 weights (label it "preview").
12. **Optional**: TomTom incidents (split the bbox into ≤ 10,000 km² tiles), OpenTopography COP30 GeoTIFF download to `output/dem_cop30.tif` (for the QGIS slope work).
13. **Output**
    - stdout: summary JSON →
```json
{
  "generated_at": "...",
  "study_area": {"name": "Chamoli", "osm_relation_id": 0, "bbox": [..], "area_km2": 0},
  "datasets": {
    "roads": {"ways": 0, "segments": 0, "total_km": 0, "by_class_km": {}},
    "landslides": {"nasa": 0, "gsi": 0, "sample": [..]},
    "accidents": {"count": 0, "black_spots": 0},
    "pois": {"hospital": 0, "police": 0, "fuel": 0},
    "weather": [{"name": "Joshimath", "rain_next_24h_mm": 0, "rain_factor": 0}],
    "incidents": {"enabled": false, "count": 0}
  },
  "risk_preview": {"by_class_km": {}, "top_10_segments": [..]},
  "warnings": ["gsi_landslides.geojson not found — download from Bhukosh", "..."]
}
```
   - files: `output/boundary.geojson`, `output/roads_segments.geojson`, `output/landslides.geojson`, `output/accidents.geojson`, `output/pois.geojson`, `output/weather.json`, `output/summary.json`, `output/segments.csv`.
### 13.4 Sanity checks on "does the data look right?"
- Boundary area ≈ 7,700 km² (approx.); bbox within lon 78.9–80.1 / lat 29.9–31.1.
- NH-7 (`ref` contains "7" / name contains "Badrinath") is present and continuous Karnaprayag → Badrinath.
- Total drivable road km is plausible (hundreds to a few thousand km).
- Elevations: ~700–900 m near Karnaprayag up to ~3,100 m at Badrinath.
- Landslide points cluster along the Alaknanda valley / NH-7 (Pipalkoti, Helang, Joshimath, Lambagad areas).
- Weather values are non-negative; monsoon months show much higher rain.
- Open all GeoJSON files in QGIS over an OSM basemap and check them visually.
---
 
## 14. Suggested repository structure
 
```
safeyatra/
├── README.md
├── SAFEYATRA_PROJECT_CONTEXT.md        ← this file
├── docker-compose.yml                  ← postgis + api + web
├── .env.example                        ← TOMTOM_API_KEY, OPENTOPO_API_KEY, DB_URL, CONTACT_EMAIL
├── data/
│   ├── manual/                         ← Bhukosh exports, accidents.csv, closures.csv
│   └── raw/                            ← DEM tiles, PBF extracts (git-ignored)
├── cache/                              ← API response cache (git-ignored)
├── output/                             ← generated GeoJSON/GPKG/CSV/TIF (git-ignored)
├── scripts/
│   ├── fetch_chamoli_data.py           ← step 1 (this spec)
│   ├── compute_slope.py                ← DEM → slope raster (rasterio/richdem)
│   ├── build_segments.py               ← GeoPandas version of attribute extraction
│   ├── compute_risk.py                 ← static risk + classes
│   └── export_gpkg.py                  ← final GeoPackage/GeoTIFF/CSV for team
├── qgis/
│   └── safeyatra.qgz                   ← QGIS project with styled layers + map layouts
├── backend/
│   ├── app/
│   │   ├── main.py                     ← FastAPI app
│   │   ├── routing.py                  ← graph load + A*
│   │   ├── risk.py                     ← dynamic multiplier
│   │   ├── updaters/weather.py         ← hourly Open-Meteo job
│   │   ├── updaters/incidents.py       ← TomTom/HERE (optional)
│   │   ├── models.py, db.py
│   │   └── routers/ (route.py, hazards.py, reports.py, admin.py)
│   └── tests/
├── frontend/
│   ├── src/ (App.tsx, components/Map.tsx, RoutePanel.tsx, SafetySlider.tsx, Legend.tsx, ReportModal.tsx)
│   └── package.json
└── notebooks/
    ├── 01_explore_data.ipynb
    ├── 02_risk_model.ipynb
    └── 03_astar_prototype.ipynb
```
 
---
 
## 15. API design (backend)
 
| Method & path | Purpose | Key params / response |
|---|---|---|
| `GET /health` | Health check | |
| `GET /places?q=` | Search Chamoli places (local list + Nominatim fallback) | `[{name, lat, lon}]` |
| `GET /route` | Safe route | `from=lat,lon&to=lat,lon&safety=0..10&avoid_night=bool` → `{safe_route, shortest_route, comparison, hazard_stretches, weather_alerts, nearest_help}` (GeoJSON) |
| `GET /segments` | Risk-coloured road layer | `bbox=…&min_risk=…` → GeoJSON FeatureCollection (or vector tiles later) |
| `GET /hazards` | Landslides, accidents, black spots | `type=landslide|accident&bbox=` |
| `GET /weather` | Current weather risk per point | |
| `GET /pois` | Hospitals/police/fuel | `bbox=&category=` |
| `POST /reports` | User report | `{type, lat, lon, description, photo}` |
| `GET /admin/reports`, `PATCH /admin/reports/{id}` | Verify/reject | auth required |
| `POST /admin/closures` | Add closure | auth required |
 
On startup: load `road_segments` into a NetworkX graph in memory. The hourly job updates `dynamic` / `risk_now` / `closed` in the DB and in memory.
 
---
 
## 16. Frontend design
 
- **Layout:** full-screen map + left panel (desktop) / bottom sheet (mobile).
- **Panel:** From / To search → Safety slider (Fastest · Balanced · Safe · Safest) → "Find route" → result cards (Safe vs Shortest: km, time, risk badge) → list of hazard stretches (click to zoom) → weather alert banner → nearest hospitals.
- **Map layers:** risk-coloured roads (green / yellow / orange / red), landslide points, accident/black-spot points, district boundary, optional slope/hillshade. Legend + layer toggles.
- **Report button:** floating "⚠ Report blockage" → pick location → type → optional photo.
- **Accessibility:** colour-blind-safe palette with labels, large tap targets, Hindi/English toggle.
- **Performance:** simplify geometries for the web, use vector tiles if the layers get large.
---
 
## 17. Implementation phases
 
| Phase | Deliverables | Owner | Done when… |
|---|---|---|---|
| **0. Setup** | Repo, folder structure, `.env.example`, Docker PostGIS, QGIS project | All | Everyone can run the project locally |
| **1. Data collection** | `fetch_chamoli_data.py` running end to end; Bhukosh request sent; accident CSV started; DEM downloaded | GIS | Summary JSON looks right (§13.4) |
| **2. Data preparation (QGIS)** | Clipped, reprojected, cleaned layers; slope raster; fixed geometries | GIS | Layers verified visually in QGIS |
| **3. Maps** | Boundary, road network, elevation, slope, landslide, accident maps (QGIS layouts → PNG/PDF for the report) | GIS | Maps exported |
| **4. Spatial analysis + risk attributes** | `road_segments.gpkg` with all §10.2 attributes + `static_risk` | GIS | Risk map looks plausible; validation in §19 passes |
| **5. Routing prototype** | Notebook: graph + A\* with λ, safe vs shortest between Gopeshwar → Joshimath, etc. | Backend | Routes change sensibly with λ |
| **6. API** | FastAPI `/route`, `/segments`, `/hazards`, `/pois` | Backend | Returns GeoJSON; tests pass |
| **7. Frontend MVP** | Map + search + slider + route cards + risk layer | Frontend | Demo works end to end |
| **8. Live layers** | Weather updater, GSI alert input, reports + admin, optional TomTom | Backend + Frontend | Risk changes with rain; reports block routes |
| **9. Validation & report** | Metrics, screenshots, documentation, presentation | All | Submitted |
| **10. Expansion** | More districts, mobile app, offline mode | — | Future |
 
---
 
## 18. MVP definition
 
**In scope:**
- Static risk from **landslides (NASA + GSI when available), terrain slope, curvature** (+ accidents if the CSV is ready).
- A\* with the safety slider; safe vs shortest comparison.
- Web map with the risk-coloured road layer and route display.
- Demo routes: **Gopeshwar → Joshimath**, **Karnaprayag → Badrinath**, **Chamoli → Tharali**, **Gopeshwar → Chopta/Ukhimath direction** (the edge of the district).
**Out of scope for MVP:** live incidents, user reports, mobile app, other districts.
 
---
 
## 19. Validation & testing
 
- **Hold-out test:** keep back ~20–30% of landslide points (e.g., the most recent years). Check what % fall on/near segments classed high/very high (like a success-rate / ROC curve per class).
- **Known hotspots check:** segments near well-known chronic slide zones on NH-7 (e.g., around Pipalkoti, Helang, Joshimath, Lambagad) should score high. Confirm against news / GSI reports.
- **Accident overlap:** black spots should fall in higher risk classes.
- **Sensitivity analysis:** vary the weights ±0.05 and check the ranking stability of the top-risk segments.
- **Routing tests:** λ = 0 equals the plain shortest path; increasing λ never increases route risk; closed edges are never used; the heuristic is admissible (unit test: h ≤ true cost).
- **Unit tests:** segmentation length sums, haversine, point-in-polygon, curvature on synthetic lines, risk normalisation bounds [0, 1].
- **Visual QA in QGIS** for every exported layer.
---
 
## 20. Known limitations, risks & decisions
 
| Issue | Impact | Mitigation / decision |
|---|---|---|
| Accident data not public | Weak accident component | Black-spot PDFs + news + RTI; curvature/gradient proxy; clearly label as approximate |
| Few alternative roads in mountains | "Safer route" often = same route | Pitch as risk-aware routing + warnings + timing + nearest help |
| Live blockages lack API coverage | Can't promise real-time closures | User reports + admin panel; optional TomTom/HERE |
| GSI data via email/manual | Delay | Request on day 1; NASA COOLR as a fallback |
| DEM resolution (30–90 m) | Road gradient noisy on hairpins | Use terrain slope around the road as a hazard proxy; document it |
| OSM gaps on village roads | Incomplete graph | Flag low-quality classes; fix in OSM / QGIS if needed |
| Static weights are subjective | Questioned in viva | Justify with literature/AHP; sensitivity analysis; ML later |
| IMD API needs whitelisting | Delay | Use Open-Meteo first |
| Open-Meteo free tier is non-commercial | Licence limit | Fine for an academic project; switch to a paid / IMD source if commercialised |
| Google Maps data | ToS restrictions | Not used as a data source (see §6) |
| Overpass/Nominatim rate limits | Blocked requests | Cache, mirrors, User-Agent, delays; or a Geofabrik PBF offline |
 
---
 
## 21. Licensing & attribution
 
- **OpenStreetMap**: ODbL. Display "© OpenStreetMap contributors" on maps; share-alike applies to derived databases if distributed.
- **Copernicus DEM**: free, attribution "© DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA".
- **Open-Meteo**: CC BY 4.0, free for non-commercial use. Attribute "Weather data by Open-Meteo.com".
- **NASA COOLR / GLC**: cite Kirschbaum et al. (2015) and the Juang et al. (2019) COOLR paper.
- **GSI Bhukosh**: accept the Bhukosh terms; cite GSI.
- **ISRO Landslide Atlas / Bhuvan**: cite NRSC/ISRO.
- **TomTom/HERE**: follow their developer terms (display attribution; no long-term storage beyond what the terms allow).
---
 
## 22. Next steps
 
### Immediate (this week)
1. **Set up the repo** with the structure in §14; add `.env.example` and `requirements.txt` (`requests`, then `geopandas shapely pyproj rasterio rasterstats osmnx networkx pandas numpy`).
2. **Build and run `scripts/fetch_chamoli_data.py`** per §13 (in Claude Code):
   - start with boundary → roads → POIs → NASA landslides → weather → segmentation → elevation → attributes → risk preview;
   - print the summary JSON; write the files to `output/`;
   - check against §13.4 and open the outputs in QGIS.
3. **Register on GSI Bhukosh** and request the Chamoli Landslide Inventory + Landslide Susceptibility (NLSM) layers. Export them to GeoJSON (EPSG:4326) into `data/manual/` when they arrive.
4. **Get a free OpenTopography API key** and download the Copernicus GLO-30 DEM for the Chamoli bbox → compute the slope raster in QGIS (EPSG:32644).
5. **Start `data/manual/accidents.csv`**: Uttarakhand Transport Dept black-spot list + Road Safety Year Books + news reports for Chamoli (aim for 30–100 points to begin with).
6. (Optional) Get a **TomTom API key** and run one incident query over Chamoli to test coverage.
7. (Optional) Submit the **IMD API whitelisting** request.
### After the data looks right
8. Write the GeoPandas pipeline (`build_segments.py`, `compute_risk.py`) using the slope raster (zonal stats in a 50 m buffer) + GSI susceptibility → final `road_segments.gpkg`.
9. Make the QGIS maps (boundary, roads, elevation, slope, landslides, accidents, risk).
10. A\* prototype notebook with the λ slider; test the demo routes.
11. FastAPI backend (`/route`, `/segments`, `/hazards`, `/pois`).
12. React + Leaflet frontend MVP.
13. Add live layers: weather updater, GSI alert input, reports + admin.
14. Validation (§19), then documentation, report and presentation.
### Prompt to start in Claude Code
> "Read SAFEYATRA_PROJECT_CONTEXT.md. Set up the repo structure from §14, then implement `scripts/fetch_chamoli_data.py` exactly as specified in §13 (requests + stdlib only for now, with caching, retries and Overpass fallbacks). Run it, print the summary JSON, and check the output against the sanity checks in §13.4."
 
---
 
## 23. Reference links
 
**Data portals**
- GSI Bhukosh: https://bhukosh.gsi.gov.in
- GSI Bhusanket (landslide forecast bulletins): http://www.bhusanket.gsi.gov.in/
- ISRO Landslide Atlas of India: https://www.isro.gov.in/Landslide_Atlas_India.html
- NASA Landslides / COOLR: https://landslides.nasa.gov · https://gpm.nasa.gov/landslides/data.html
- ISRO Bhuvan thematic services: https://bhuvan-app1.nrsc.gov.in/thematic/thematic/index.php
- OpenTopography Global DEM API: https://portal.opentopography.org/apidocs/
- Geofabrik India extracts: https://download.geofabrik.de/asia/india.html
- Uttarakhand Transport Dept road safety cell: https://transport.uk.gov.in/pages/view/70-roadsafetycell
- eDAR / iRAD (IIT Madras CoERS): https://coers.iitm.ac.in/irad/
**APIs**
- Nominatim: https://nominatim.org/release-docs/latest/api/Search/ (usage policy: https://operations.osmfoundation.org/policies/nominatim/)
- Overpass API: https://wiki.openstreetmap.org/wiki/Overpass_API
- OSMnx: https://osmnx.readthedocs.io
- Open-Meteo: https://open-meteo.com/en/docs · Elevation: https://open-meteo.com/en/docs/elevation-api · Archive: https://open-meteo.com/en/docs/historical-weather-api
- IMD API: https://api.imd.gov.in/public/api_reference.html · Whitelisting: https://city.imd.gov.in/citywx/api_request.php
- TomTom Traffic Incidents: https://developer.tomtom.com/traffic-api/documentation/traffic-incidents/incident-details
- HERE Traffic v7: https://docs.here.com/traffic-api/
- Google Routes API (traffic on polyline only, for reference): https://developers.google.com/maps/documentation/routes
**Libraries**
- GeoPandas https://geopandas.org · Shapely https://shapely.readthedocs.io · Rasterio https://rasterio.readthedocs.io · rasterstats https://pythonhosted.org/rasterstats/ · NetworkX A\* https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.astar.astar_path.html · pgRouting https://pgrouting.org · FastAPI https://fastapi.tiangolo.com · Leaflet https://leafletjs.com · MapLibre https://maplibre.org
**Key papers**
- Kirschbaum, Stanley & Zhou (2015), *Spatial and temporal analysis of a global landslide catalog*, Geomorphology 249:4–15.
- Juang, Stanley & Kirschbaum (2019), *Using citizen science to expand the global map of landslides: Introducing COOLR*, PLOS ONE 14(7): e0218657.
 
