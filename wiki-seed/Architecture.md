# Architecture

Richmack Georgia is a Flask/SQLite application with a Leaflet browser client and Docker-based production runtime.

## High-Level Architecture
```text
Browser
  |
Nginx + HTTPS
  |
127.0.0.1:5075
  |
Docker: richmack-georgia
  |
Flask
  |
SQLite
  |
/app/data
  |
Host bind mount: ./data
```

## Stack
- Backend: Flask
- Database: SQLite
- Map rendering: Leaflet
- Basemap: OpenStreetMap
- Overlays: GeoJSON
- Host: AWS Lightsail / Ubuntu
- Reverse proxy: Nginx
- TLS: Let's Encrypt / Certbot
- Runtime: Docker Compose
- CI/CD: GitHub Actions
- Server deploy command: `richdeploy georgia`

## Important Files
```text
app/
├── __init__.py
├── db.py
├── phase5.py
└── routes.py
run.py
requirements.txt
Dockerfile
docker-compose.yml
```

## Persistence
Production state is bind-mounted with:
```text
./data:/app/data
```
This protects users, parent/student links, grades, game attempts, assignments, academic years, skill evidence, constructed responses, and usage events across container replacement.

## Logical Data Domains
### Identity and Family
Users, roles, invitations, parent/student links, passwords, and feature restrictions.

### Curriculum
Courses, modules, lessons, assessment items, and verified sources.

### Assessment
Progress, provisional/final scores, constructed submissions, game attempts, and mastery.

### Skills
Skill definitions, lesson-skill mappings, and game-skill evidence.

### Academic Administration
Assignments and academic years.

### Usage
Activity events, durations, and last-active information used in reports.

## Role Model
Roles are `admin`, `parent`, and `student`. Authorization is enforced server-side; hiding links in the UI is not considered sufficient security.

## Why SQLite
SQLite keeps resource usage low and backups simple on a small Lightsail host. The application is structured so a future Postgres/PostGIS migration remains possible if scale requires it.
