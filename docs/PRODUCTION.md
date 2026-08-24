# Production deployment

Production URL: `https://georgia.richmackos.com`

Production directory: `/home/ubuntu/richmack-georgia`

Backend: `127.0.0.1:5075`

Persistent data: `/home/ubuntu/richmack-georgia/data` mounted at `/app/data`.

## Normal deployment

A push to `main` runs CI, syncs the repository while preserving `.env`, `data/`, and `backups/`, then calls:

```bash
richdeploy georgia
```

The workflow finishes by verifying `https://georgia.richmackos.com/health`.

## Required GitHub Actions secrets

- `RICHMACK_DEPLOY_KEY`
- `RICHMACK_DEPLOY_HOST`
- `RICHMACK_DEPLOY_USER`

The deployment key must never be committed to this repository.
