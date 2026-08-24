# Security and Privacy

## Never Commit
`.env`, production passwords, AWS credentials, SSH private keys, GitHub deployment secrets, API tokens, production databases, or student records.

## Parent Isolation
Authorization is server-side and deny-by-default. UI hiding is not security.

## Passwords
Store secure hashes, not plaintext. Temporary reset credentials should be short-lived.

## Invites
Parent invites and Family Link Codes should be scoped, time-limited, and one-time where appropriate.

## Deployment Persistence
Deployment must preserve `.env`, `data/`, and `backups/`. The database must never exist only in a disposable container layer.

## Network Boundary
Nginx terminates HTTPS and proxies to the localhost backend. Flask/Gunicorn should not be exposed directly to the internet in the normal production architecture.
