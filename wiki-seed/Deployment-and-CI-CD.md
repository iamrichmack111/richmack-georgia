# Deployment and CI/CD

## Production
- URL: https://georgia.richmackos.com
- Host: AWS Lightsail / Ubuntu
- Production directory: `/home/ubuntu/richmack-georgia`
- Backend: `127.0.0.1:5075`
- Container: `richmack-georgia`

## Normal Push-to-Deploy Flow
```text
git push origin main
→ CI compile/tests/GeoJSON/Docker build
→ production sync
→ richdeploy georgia
→ Docker rebuild/recreate
→ readiness check
→ public /health verification
```

A failed CI gate prevents deployment. This was verified when pytest initially failed to import `app`; production did not continue until the import-path configuration was fixed.

## Pytest Configuration
```ini
[pytest]
pythonpath = .
testpaths = tests
```
CI runs `python -m pytest -q`.

## richdeploy
`richdeploy georgia` runs on the Lightsail server. It requires `.env`, preserves/backs up persistent data, compiles Python, builds Docker, recreates the service, polls `/health`, and prints logs on failure.

## Database
Production database: `data/georgia.db`. The deploy wrapper must back up the real filename.

## First Deployment vs Update
First deployment may require `r53sub`, DNS verification, Nginx, and Certbot. Normal updates should not recreate DNS/TLS; they should flow through GitHub Actions and `richdeploy georgia`.

## Production Checks
Backend: `curl -fsS http://127.0.0.1:5075/health`

Public: `curl -fsS https://georgia.richmackos.com/health`
