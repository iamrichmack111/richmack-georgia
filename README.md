# Richmack Georgia — Phase 3 (v0.3)

Phase 3 turns the atlas prototype into a deeper Georgia Studies curriculum test for ages 9–14.

## What changed

- Two complete deep modules: **Georgia Water Systems** and **Transportation & Logistics**.
- Eight coursework lessons with objectives, explanatory reading, worked examples, and remediation.
- Multi-step numeric word problems and genuine constructed-response critical thinking.
- Mastery raised to **85%** for auto-graded work.
- Constructed responses are **not falsely auto-graded**. They enter an admin review queue with a 0–4 rubric.
- Final lesson grade = **70% objective/quantitative score + 30% rubric score** once all required written responses are reviewed.
- Statuses: not started → remediation / provisional → mastered.
- CSV export contains auto score, final score, status, module, and course.
- Phase 2 Leaflet/OSM systems atlas and Map Hunt remain included.

## Local install

```bash
cd ~/Downloads
unzip richmack-georgia-v0.3.zip
cd richmack-georgia-v0.3

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

### Default local accounts

- Admin: `admin` / `change-me-local`
- Student: `student` / `student`

Admin review queue: `http://127.0.0.1:5075/admin`

## Test

```bash
source .venv/bin/activate
pytest -q
curl -s http://127.0.0.1:5075/health
```

## Phase 3 test path

1. Log in as `student`.
2. Open **Module 1 — Georgia Water Systems**.
3. Complete Lessons 1.1–1.4. A score below 85% produces remediation.
4. Strong objective work plus a written response produces **provisional** status.
5. Log out and sign in as `admin`.
6. Review the constructed response against the rubric and assign 0–4.
7. The system recalculates the final score; 85% or higher becomes **mastered**.
8. Export grades from the admin portal.

## Source policy

Seed coursework is grounded in official sources in the built-in registry: Georgia EPD, GDOT, Georgia Ports Authority, Georgia Department of Education, and U.S. Census Bureau. Simplified numerical freight rates in practice problems are explicitly fictional and are used only to teach quantitative reasoning.
