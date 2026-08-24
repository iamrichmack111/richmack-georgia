# Architecture

- Flask application
- SQLite persistence
- Leaflet map UI with OpenStreetMap basemap
- GeoJSON educational layers
- Docker / Docker Compose
- Nginx reverse proxy
- Let's Encrypt TLS
- GitHub Actions CI/CD

Production application data is bind-mounted from `./data` to `/app/data` so accounts, grades, assignments, and analytics survive container replacement.
