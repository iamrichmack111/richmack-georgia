# Deployment

Normal production updates are push-to-deploy:

1. Push to `main`.
2. GitHub Actions runs tests.
3. Code is synced to `/home/ubuntu/richmack-georgia` while preserving `.env`, `data/`, and `backups/`.
4. The server runs `richdeploy georgia`.
5. Public health is verified at `https://georgia.richmackos.com/health`.

DNS/Nginx/Certbot are bootstrap infrastructure and should not be rerun for every code update.
