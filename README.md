# Richmack Georgia — Phase 5 (v0.5)

Phase 5 expands the working Phase 4.1 family-safe Georgia Studies platform into a deeper long-term learning system for ages 9–14.

## What Phase 5 adds

- **Skill-level analytics** across physical regions, mountains, rivers, watersheds, reservoirs, water quality, transportation, economics, industry, quantitative reasoning, historical causation, source analysis, and critical thinking.
- **Map Hunt skill evidence**: game attempts can now record which skill areas were right or wrong rather than only the overall score.
- **Four new deep modules / 12 lessons**:
  - Module 3 — Physical Geography & Mountains
  - Module 4 — Rivers, Lakes & Watersheds
  - Module 5 — Georgia History: Place, Change & Evidence
  - Module 6 — Georgia Economics & Business
- **Age-aware coursework**: students see lessons appropriate to their configured age within the 9–14 curriculum range.
- **Assignments**: admins and linked parents can assign either a whole module or one lesson, set a minimum score, and optionally set a due date.
- **Academic years**: grades and new game attempts are attached to an academic year. The default local year is `2026–2027`; admins can create future years and activate one without deleting old records.
- **Academic-year gradebook**: view old/current year records separately while keeping the existing all-history CSV export.
- **Student assignment dashboard**: students see assigned work, target mastery, due dates, progress, and completion/overdue state.
- **Parent/admin reports**: student reports now include skill-by-skill mastery, assignments, existing usage statistics, grades, games, and improvement recommendations.
- Existing deny-by-default parent privacy, Family Link Codes, password reset tools, user restrictions, verified source registry, Leaflet/OSM atlas, and 85% mastery model remain intact.

## Local install

```bash
cd ~/Downloads
unzip richmack-georgia-v0.5.zip
cd richmack-georgia-v0.5

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

Open `http://127.0.0.1:5075`.

### Default local test accounts

- Admin: `admin` / `change-me-local`
- Age 12 student: `student` / `student`
- Age 14 student: `student14` / `student14`

## Recommended Phase 5 test

1. Log in as admin.
2. Open **Admin** and assign **Module 3 — Physical Geography & Mountains** to `Age 14 Test Student`, target 85%.
3. Log in as `student14` and confirm **My Assignments** appears on the dashboard.
4. Complete lesson 3.2 or 6.2 to test a numeric problem plus constructed response.
5. Play Map Hunt once to generate map-skill evidence.
6. Return as admin and open the student's **Analytics** page. Confirm the skill bars show evidence counts and scores.
7. Open **Gradebook** and confirm the records appear under academic year `2026–2027`.
8. Create a future academic year in Admin, activate it, take another test, and confirm the new event appears under that year while the older record remains in 2026–2027.

## Parent assignment test

A parent can assign only a student already linked to that parent account. Parent access remains deny-by-default; assignment controls do not provide a student directory or expand grade visibility.

## Academic-year behavior

The active year controls where **new** grade/game records and assignments are stored. Changing the active year does not rewrite historical records.

## Verified-source architecture

The source registry includes official/authoritative material from Georgia Department of Education, Georgia Environmental Protection Division / Georgia Geologic Survey, Georgia Department of Transportation, Georgia Ports Authority, Georgia Archives, U.S. Census Bureau, and Georgia Department of Economic Development. Fictional numerical scenarios are labeled and are used to teach reasoning rather than presented as current operating data.

## Verification

```bash
source .venv/bin/activate
pytest -q
curl -s http://127.0.0.1:5075/health
```

Expected health response:

```json
{"app":"richmack-georgia","phase":"5.0","status":"ok"}
```

## LAN testing

For testing parent/student accounts from another device on the same Wi-Fi:

```bash
export HOST=0.0.0.0
python run.py
```

Then find the Mac's LAN IP with `ipconfig getifaddr en0` (or `en1`) and open `http://<LAN-IP>:5075` from the other device.
