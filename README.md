# Richmack Georgia — Local Phase 2 / v0.2

Phase 2 upgrades the original point-based prototype into an interactive Georgia systems atlas for ages 9–14.

## What changed

- Layered Leaflet atlas with simplified polygons and lines instead of captioned blue dots
- Physiographic regions, mountains, rivers, reservoir, cities, interstates, rail, airport, port, dam, logistics
- Clickable feature detail cards explaining **what it is** and **why it matters**
- Layer toggles and map legend
- Playable 10-question randomized **Map Hunt: Systems Atlas**
- Persistent `game_attempts` records for student map-game scores
- Dashboard best-game score
- Phase-2 source registry additions for GDOT maps and Georgia EPD geologic maps
- Data structure remains ready for full official GIS shapefile/GeoJSON imports

## Verified references used for the atlas design

- Georgia EPD Water Supply Watersheds: https://epd.georgia.gov/water-supply-watersheds
- Georgia EPD GIS databases: https://epd.georgia.gov/geographic-information-systems-gis-databases-and-documentation
- Georgia EPD Geologic Survey Maps: https://epd.georgia.gov/outreach/publications/georgia-geologic-survey-maps
- Georgia DOT road and traffic data: https://www.dot.ga.gov/GDOT/Pages/RoadTrafficData.aspx
- Georgia DOT highway and transportation maps: https://www.dot.ga.gov/GDOT/Pages/Maps.aspx

The bundled Phase-2 geometries are intentionally simplified educational representations, not survey/navigation data. The next GIS-ingest step can replace these geometry records with official source shapefiles without changing the map/game architecture.

## Upgrade / unzip

To preserve your current v0.1 folder, unpack Phase 2 beside it:

```bash
cd ~/Downloads
unzip richmack-georgia-v0.2.zip
cd richmack-georgia-v0.2
```

## Fresh local run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
set -a
source .env
set +a

python run.py
```

Open http://127.0.0.1:5075

Default development accounts:

- Admin: `admin` / `change-me-local`
- Student: `student` / `student`

## Run tests

```bash
source .venv/bin/activate
pytest -q
```

## Test Phase 2 manually

1. Sign in as `student`.
2. Open **Map**.
3. Toggle Land Regions, Mountains, Water, Transportation, Infrastructure, and Cities independently.
4. Click lines and polygons, not just points, and verify the feature explanation changes.
5. Open **Games → Map Hunt**.
6. Complete ten challenges.
7. Return to the student dashboard and verify the best map-game score appears.
8. Sign in as admin and confirm regular grade CSV export still works.

## Reset the local database

```bash
rm -f data/georgia.db
python run.py
```
