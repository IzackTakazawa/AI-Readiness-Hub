# Base44 Dev Environment

## Project
Static single-page HTML app ("DART Pilot Student AI Readiness and Integration Hub"). No backend, no build step, no dependencies, no external API keys — all assistant behaviors are local/prototype (per README).

## Running
- `docker compose -f docker-compose.base44.yml up -d`
- nginx:alpine serves the repo root (bind-mounted read-only) on host port 3000.
- Health: `curl http://localhost:3000/` → 200.

## Notes
- The repo root directory must be world-traversable (chmod 755) so the nginx worker user can read the bind-mounted files. If you get 403 Forbidden, run `chmod 755 .` at the repo root.
- Edits to `index.html` are live immediately (static file); call `reload_preview` to refresh the user's browser.
