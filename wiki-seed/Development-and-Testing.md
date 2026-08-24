# Development and Testing

## Local Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
set -a; source .env; set +a
python run.py
```
Open `http://127.0.0.1:5075`.

## Test Accounts
- Admin: `admin / change-me-local`
- Student: `student / student`
- Age 14 student: `student14 / student14`

## Tests
```bash
python -m compileall -q app run.py
python -m pytest -q
curl -s http://127.0.0.1:5075/health
```

## Recommended Regression Areas
- parent isolation and direct-URL denial
- lesson and game gradebook records
- CSV exports
- password reset/change flow
- assignments and academic-year separation
- map geometry/visibility
- Map Hunt repetition

## LAN Testing
Use `HOST=0.0.0.0`, find the Mac LAN IP with `ipconfig getifaddr en0`/`en1`, and open that address from another device on the same Wi-Fi.

A passing `/health` is necessary but not sufficient; important database-backed routes should also be tested.
