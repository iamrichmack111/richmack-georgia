# Richmack Georgia — Local v0.1

An evergreen Georgia Studies learning platform for ages 9–14. The prototype includes:

- Flask + SQLite local-first architecture
- Leaflet + OpenStreetMap interactive Georgia map
- Local educational GeoJSON overlay data
- Structured courses, lessons, quizzes, source records, mastery, and grade history
- Student dashboard
- Admin/parent portal
- CSV grade export by student or for all students
- Verified-source registry with refresh intervals
- Age-layered lesson design
- Starter game area designed to expand into persistent game modules
- Automated pytest smoke/integration tests

## Verified seed sources

The initial seed content is deliberately small and uses official sources:

1. Georgia Department of Education — Social Studies: https://gadoe.org/learning/social-studies/
2. Georgia Environmental Protection Division — Watershed Protection Branch: https://epd.georgia.gov/about-us/watershed-protection-branch
3. Georgia EPD — Water Supply Watersheds/GIS: https://epd.georgia.gov/water-supply-watersheds
4. Georgia Department of Transportation — Road & Traffic Data: https://www.dot.ga.gov/GDOT/Pages/RoadTrafficData.aspx
5. U.S. Census Bureau — QuickFacts Georgia: https://www.census.gov/quickfacts/fact/table/GA/PST045223

The app keeps source metadata separate from lesson text so future import/update jobs can refresh changing statistics without rewriting the platform.

## Unzip and run on macOS/Linux

```bash
unzip richmack-georgia-v0.1.zip
cd richmack-georgia

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

Open:

- App: http://127.0.0.1:5075
- Health: http://127.0.0.1:5075/health

Local demo accounts from `.env.example`:

- Admin: `admin` / `change-me-local`
- Student: `student` / `student`

These are development-only credentials. Change them before any network/cloud deployment.

## Run tests

```bash
cd richmack-georgia
source .venv/bin/activate
pytest -q
```

Expected result for v0.1: four passing tests.

## Quick curl smoke test

```bash
curl -s http://127.0.0.1:5075/health
```

Expected JSON:

```json
{"app":"richmack-georgia","status":"ok"}
```

## Reset local data

```bash
rm -f data/georgia.db
python run.py
```

The database is recreated and reseeded on startup.

## Grade exports

Sign in as the admin and use **Export All Grades CSV**, or export an individual student's history from the student table. Grade events are append-only attempts; progress/mastery records keep each student's best score and current mastery.

## Mapping architecture

Leaflet is the browser map engine. OpenStreetMap provides the default basemap. Curriculum features live independently in `app/static/data/georgia_features.geojson`, so they can later be replaced with official county boundaries, river networks, watershed polygons, treatment facilities, road/rail layers, historical sites, and other verified datasets. Keeping curriculum overlays separate also makes future offline maps possible.

## Indefinite-growth design

New material is data, not hard-coded pages:

`source -> course -> lesson -> question/activity -> grade event -> mastery`

Future migrations can add academic years, assignments, standards alignment, all 159 counties, game attempt tables, GIS ingest jobs, PDF report cards, teacher accounts, and offline tile packages without changing the fundamental architecture.

## Recommended v0.2

- Import official Georgia county boundaries and watershed polygons
- Add assignments/due dates and academic-year archives
- Add standards tags to lessons
- Add fully scored Map Hunt and Water System Chain games
- Add student creation/editing in admin
- Add PDF report cards/transcripts
- Add source-update jobs with dataset checksums and last-refresh status
