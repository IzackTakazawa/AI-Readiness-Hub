# Base44 Dev Environment

## Project
Static single-page HTML app ("DART Pilot Student AI Readiness and Integration Hub") with a Python FastAPI + SQLite backend that persists readiness assessment results.

## Architecture
- **Frontend:** `index.html` — static SPA served by nginx. No build step.
- **Backend:** `backend/main.py` — FastAPI app with SQLite. Endpoints:
  - `POST /api/assessments` — save an assessment result
  - `GET /api/assessments` — list all saved assessments (newest first)
  - `GET /api/health` — health check
- **Proxy:** nginx proxies `/api/` to the FastAPI service (single-origin, no CORS issues).
- **Database:** SQLite at `backend/data/readiness.db` (stored in a Docker volume `api_data`).

## Running
- `docker compose -f docker-compose.base44.yml up -d`
- nginx serves the frontend on host port 3000 and proxies API calls to the FastAPI service.
- Health: `curl http://localhost:3000/api/health` → `{"status":"ok"}`.

## Notes
- The repo root directory must be world-traversable (chmod 755) so the nginx worker user can read the bind-mounted files. If you get 403 Forbidden, run `chmod 755 .` at the repo root.
- Frontend edits to `index.html` are live immediately (static file); call `reload_preview` to refresh the user's browser.
- Backend edits are live via `uvicorn --reload`; call `reload_preview` if the user needs to see the effect.
- The backend volume mount must NOT be read-only (`:ro`) because the data volume mount point needs to be created at container init.
