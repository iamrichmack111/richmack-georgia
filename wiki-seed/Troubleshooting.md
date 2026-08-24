# Troubleshooting

## `ModuleNotFoundError: No module named app` in CI
Ensure `pytest.ini` contains `pythonpath = .` and run tests using `python -m pytest -q`.

## CI Green but Site Did Not Change
Run `gh run list --limit 10` and verify both CI and Deploy production succeeded. Use `gh run view RUN_ID --log-failed` for failures.

## Backend Down
```bash
cd /home/ubuntu/richmack-georgia
docker compose ps
docker compose logs --tail=120
curl -i http://127.0.0.1:5075/health
```

## Backend Healthy, Public Site Fails
Check `sudo nginx -t`, reload Nginx, then curl HTTP/HTTPS public endpoints.

## Certbot NXDOMAIN
Run `dig +short georgia.richmackos.com A`; do not run Certbot until the hostname resolves to the Lightsail IP.

## Wiki Seeder Deletes `.git`
The rsync command must use `--exclude '.git/'` when copying into the cloned Wiki repo.

## Wiki Clone Says Repository Not Found
Create the first Wiki page once in GitHub's UI so the `.wiki.git` repo exists, then rerun the seeder.

## Wrong Parent Visibility
Inspect explicit parent/student links. Do not restore the old all-students invite behavior.

## Data Lost After Container Rebuild
Verify the bind mount `./data:/app/data` and the real production DB `data/georgia.db`.
