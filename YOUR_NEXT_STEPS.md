# SafeYatra: Your Next Steps

> These are the tasks **only you can do**: they need a website login, your email, or your eyes on the map.
> Everything else (slope raster, GeoPackage, risk score, routing, backend, frontend) Claude does.
> Last updated: 24 Nov 2026

---

## Summary

| # | Task | Feature it is for | Priority | Time |
|---|---|---|---|---|
| 0 | **Create a Clerk app and paste the key in `.env`** (steps in `README.md` → "Sign-in") | Sign-in, Report a blockage, Admin page | 🔴 **Do first** | 10 min |
| 1 | Request GSI landslide data | Risk map, risk score, safe routing | 🟢 **Optional now**: replaced by NASA's global susceptibility map (already downloaded to `data/raw/nasa_susceptibility/`). Do this only if you have spare time | 30 min + days of waiting |
| 2 | Convert the GSI data when it arrives | Same as above | 🟢 Only if #1 is done | 15 min |
| 3 | ~~Install QGIS on Windows~~ ✅ Done (QGIS 3.44.15 LTR) | Checking data, report maps, viva demo | — | — |
| 4 | Check Claude's results in QGIS | Quality check of risk map and slope | 🟡 After Claude finishes | 15 min each |
| 5 | Make the report maps | Project report and presentation | 🟡 Or let Claude script them | 1–2 hours |
| 6 | Get an OpenTopography API key | Better slope / elevation | 🟢 Optional | 5 min |
| 7 | Collect seasonal road closure dates | Road closures feature | 🟢 Optional | 30 min |
| 8 | Get a TomTom API key | Live traffic incidents | 🟢 Optional, probably skip | 10 min |
| 9 | Learn how to read GSI forecast bulletins | GSI landslide warning (monsoon) | 🟢 Later, before the demo | 15 min |

Each time you finish a task, **tell Claude** (see the "Then tell Claude" line in each task).

---

## 1. Request the GSI landslide data 🔴

**What it is for:**
- **Landslide susceptibility zones (NLSM):** the biggest factor in the risk score (**30% of the weight**). Without it, the risk is based only on past landslides, slope and bends.
- **Landslide inventory:** official landslide locations. It balances our news-based data, which over-counts busy places like Nandprayag.
- **Features that improve:** the risk map, segment risk details, safest-route search and the dangerous-stretch warnings.

**Website:** https://bhukosh.gsi.gov.in (Geological Survey of India, free)

**Steps:**
1. Open https://bhukosh.gsi.gov.in in Chrome or Edge.
   - If it doesn't load: **turn off any VPN**, try **mobile data (phone hotspot)** or **college Wi-Fi**, and try another browser.
   - The main GSI site https://www.gsi.gov.in works, so you can confirm GSI itself is online.
2. Click **Register** (top right). Fill in the form with your details. As the purpose, write something like *"Academic final-year project on landslide risk in Chamoli district"*.
3. Open the confirmation email from GSI and click the link to activate your account.
4. Go back to the site and **Log in**.
5. Open the **map viewer** (look for "Map", "Spatial Data" or "Data Download").
6. In the layer or theme list, find **Landslide** and select both:
   - ☐ **Landslide Inventory**
   - ☐ **Landslide Susceptibility** (may be called "NLSM" or "National Landslide Susceptibility Mapping")
7. Choose the area: **Uttarakhand → Chamoli**. If you can't select a district, choose **Uttarakhand**, and Claude will cut out Chamoli.
8. Click **Add to Cart**, open the cart and **Submit / Checkout**.
9. Wait for the email with the download link. This can take a few hours or a few days.

> Menu names on the website may differ slightly. Look for the words **Landslide**, **Cart** and **Download**.

**If the site is still down after 2–3 days:**
- Ask your **project guide** or the **college GIS / geology lab**. They often already have GSI data.
- Backup, for viewing only: ISRO Landslide Atlas, https://www.isro.gov.in/Landslide_Atlas_India.html (PDF maps, can be cited in the report).

**Then tell Claude:** "GSI request sent", and later "GSI data arrived".

---

## 2. Convert the GSI data when it arrives 🔴

**What it is for:** the data script reads GeoJSON files in a fixed place. Once they are there, the 30% susceptibility weight switches on automatically.

**Easy option (recommended):**
1. Download the zip from the GSI email.
2. Unzip it into `gisproject\data\raw\gsi\` (create the `gsi` folder if it doesn't exist).
3. **Tell Claude:** "GSI files are in data/raw/gsi". Claude converts them with Python.

**QGIS option (if you want to do it yourself):**
1. Open QGIS. Go to **Layer → Add Layer → Add Vector Layer…**, choose the `.shp` file, and click **Add**.
2. Right-click the layer in the Layers panel → **Export → Save Features As…**
3. Set:
   - **Format:** `GeoJSON`
   - **File name:**
     - Susceptibility layer → `gisproject\data\manual\gsi_susceptibility.geojson`
     - Inventory layer → `gisproject\data\manual\gsi_landslides.geojson`
   - **CRS:** `EPSG:4326 - WGS 84`
4. Click **OK**. Do this once for each layer.
5. **Tell Claude:** "GSI GeoJSON files are in data/manual".

---

## 3. Install QGIS on Windows 🟡

**What it is for:** `qgis/safeyatra.qgz` is only the *project file* (like a .docx). You need the QGIS *program* to open it. QGIS is not installed on this computer.
- Checking that the data and risk map look right
- Making report maps (task 5)
- Showing GIS work in your **viva**

**Website:** https://qgis.org/download

**Steps:**
1. Open https://qgis.org/download.
2. Under **Windows**, download **QGIS Long Term Release (LTR)**, the standalone installer (`.msi`, about 1 GB).
3. Run the installer, click **Next** on every screen, then **Install**. Wait about 10 minutes.
4. Open **QGIS Desktop** from the Start menu.
5. Go to **Project → Open…** and choose `C:\Users\Aditya\Desktop\gisproject\qgis\safeyatra.qgz`.
6. The project was made on Linux, so a **"Handle Unavailable Layers"** window may appear. If it does:
   - Click **Auto-Find**.
   - If some layers are still red, click **Browse** next to each one and pick the matching file in `gisproject\output\`.
   - Click **Apply Changes**.
7. Go to **Project → Save**.

**Then tell Claude:** "QGIS installed".

---

## 4. Check Claude's results in QGIS 🟡

**What it is for:** a GIS developer must visually confirm the data is correct. A good screenshot for the report, too.

Do this **after** Claude says each step is finished.

### 4a. Slope map (after Claude makes the slope raster)
1. In QGIS: **Layer → Add Layer → Add Raster Layer…** → `gisproject\output\slope_32644.tif` → **Add**.
2. Right-click the layer → **Properties → Symbology** → Render type: **Singleband pseudocolor** → Color ramp: **Spectral** (inverted) or **Reds** → **OK**.
3. **Check:** steep valley walls should look bright or red, and flat valley floors and river beds dark. The Badrinath valley floor should be flatter than the slopes around it.

### 4b. GeoPackage and risk map (after Claude makes `road_segments.gpkg`)
1. Drag `gisproject\output\road_segments.gpkg` into QGIS. Select **all layers** and click **Add**.
2. Right-click `road_segments` → **Properties → Symbology** → **Categorized** → Value: `risk_class` → **Classify** → **OK**.
3. **Check:** these known danger spots on NH-7 should be orange or red:
   Nandprayag · Pagal Nala · Patalganga · Helang · Lambagad · Bhanerpani · Kameda
4. **Check:** roads stop at the district boundary (they were not clipped before).

**Then tell Claude:** "Looks good" or "Something looks wrong at ___".

---

## 5. Make the report maps 🟡

**What it is for:** the project report and presentation need about 7 proper maps (GIS Developer workflow step 3).

> **Shortcut:** say **"Claude, make the maps"** and Claude will generate all 7 PNGs with a script. Do the steps below only if you want to make them in QGIS yourself (good practice for the viva).

**Maps to make:**

| File name | Layers to turn on |
|---|---|
| `01_boundary.png` | boundary + OpenStreetMap basemap |
| `02_road_network.png` | boundary + roads (Categorized by `highway`) |
| `03_elevation.png` | boundary + DEM (`dem_32644.tif`) |
| `04_slope.png` | boundary + slope (`slope_32644.tif`) |
| `05_landslides.png` | boundary + roads (grey) + landslides (Categorized by `source`) |
| `06_rivers.png` | boundary + roads (grey) + rivers |
| `07_risk_map.png` | boundary + roads (Categorized by `risk_class`) |

**Steps for each map:**
1. Turn on only the layers listed for that map (tick boxes in the Layers panel).
2. Go to **Project → New Print Layout…**, type a name (e.g., `Risk map`) and click **OK**.
3. **Add Item → Add Map**, then drag a box over most of the page.
4. **Add Item → Add Legend**, then click to place it.
5. **Add Item → Add Scale Bar**, then place it.
6. **Add Item → Add North Arrow**, then place it.
7. **Add Item → Add Label** for the title (e.g., *"Road Risk Map, Chamoli District"*).
8. **Add Item → Add Label** again for the credit line, small font:
   *"© OpenStreetMap contributors · NASA Global Landslide Catalog · Terrain: Mapzen/SRTM"*
9. **Layout → Export as Image…** → save in `gisproject\maps\` (create the folder) with the file name from the table.

**Then tell Claude:** "Maps done".

---

## 6. Get an OpenTopography API key 🟢 Optional

**What it is for:** downloads the **Copernicus 30 m elevation model**, which is slightly better than the free tiles Claude uses now. It improves the **slope map** and **elevation profiles**. The project works without it.

**Website:** https://portal.opentopography.org

**Steps:**
1. Open https://portal.opentopography.org and click **Register** (top right).
2. Fill in the form (Affiliation: your college; Purpose: academic). Confirm the email.
3. Log in → click **MyOpenTopo** (top right) → **Request API Key** → copy the key.
4. In `gisproject\`, make a copy of `.env.example` and rename the copy to `.env`.
5. Open `.env` in Notepad. Fill in the line:
   ```
   OPENTOPO_API_KEY=paste_your_key_here
   ```
6. Save. **Never share this file** or post it online.

**Then tell Claude:** "OpenTopography key added".

---

## 7. Collect seasonal road closure dates 🟢 Optional

**What it is for:** the **Road closures** feature. Closed roads are removed from routing during those dates (e.g., the road beyond Badrinath in winter).

**Steps:**
1. Search the news for each road below and note when it usually closes and reopens:
   - Badrinath – Mana (winter snow; Badrinath temple closing/opening dates)
   - Joshimath – Malari (NH-107B, winter snow)
   - Govindghat – Ghangaria / Hemkund (trek route, closed in winter)
   - Gopeshwar – Chopta – Ukhimath (Tungnath area, snow)
   - Any road you know is closed often in the monsoon
2. Good sources: the Badri-Kedar Temple Committee announcements, Uttarakhand Police or Chamoli district posts, and BRO (Border Roads Organisation) news.
3. Write them in a simple table (Excel or a text file is fine):

   | Road | From place | To place | Closes (approx.) | Opens (approx.) | Source link |
   |---|---|---|---|---|---|
   | Badrinath–Mana | Badrinath | Mana | 15 Nov | 30 Apr | (news URL) |

**Then tell Claude:** "Closure list ready". Claude turns it into the data file the app uses.

---

## 8. Get a TomTom API key 🟢 Optional, probably skip

**What it is for:** **live traffic incidents** (road closures, accidents) from TomTom. Coverage in Chamoli is likely very poor, so this is only worth it if your guide asks for "live traffic".

**Website:** https://developer.tomtom.com

**Steps:**
1. Open https://developer.tomtom.com and click **Register**. Confirm the email.
2. Log in → **Dashboard** → **Keys** → copy the default key (or click **Add Key**).
3. Open `gisproject\.env` in Notepad and add the line:
   ```
   TOMTOM_API_KEY=paste_your_key_here
   ```
4. Save.

**Then tell Claude:** "TomTom key added". Claude will test whether it returns anything for Chamoli.

---

## 9. Learn how to read GSI forecast bulletins 🟢 Later

**What it is for:** the **GSI landslide warning** feature. During the monsoon (June–September), GSI publishes daily landslide forecasts for some districts. The admin (you, in the demo) enters the alert level for Chamoli in the admin panel, and the app raises the road risk.

**Website:** http://www.bhusanket.gsi.gov.in/ (slow to load; be patient)

**Steps:**
1. Open the site and find the daily forecast or bulletin for **Uttarakhand**.
2. Look for **Chamoli** and its alert level: **Low / Moderate / High**.
3. During the demo, enter that level in the app's **Admin panel → GSI alert** (Claude will build this screen).
4. Outside the monsoon there are no bulletins. For the demo, use a **pretend** alert level.

---

## What Claude is doing meanwhile (no action needed from you)

| Claude's task | Feature it is for |
|---|---|
| Proper slope raster | Better risk scores and an elevation profile |
| Clean GeoPackage (`road_segments.gpkg`) | Final GIS data for teammates |
| Final risk score (after the GSI data) | Risk map, safest route |
| Validation (hotspot check, hold-out test) | Report and viva |
| A\* routing module | Safest vs shortest route, safety slider |
| FastAPI backend | Serves routes, risk and weather to the app |
| React + Leaflet frontend | The app screens |
| Hourly weather updater | Live rain alerts and rain-adjusted risk |
| Report-a-blockage + admin panel | Blocked roads, closures, GSI alert input |
