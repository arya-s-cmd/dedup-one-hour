# Dedup in One Hour (FastAPI + React)
Quickstart: Dockerized backend + frontend with seed data and an append-only, hash-chained audit log.

## Prereqs
- Install **Docker Desktop** (Windows/Mac) or Docker Engine (Linux).
- Port 8000 and 5173 free.

## Run
```bash
docker compose up --build
```
Open:
- UI: http://localhost:5173
- API docs: http://localhost:8000/docs

In the UI:
1) Click **Run Deduplication**.
2) Review a few suggested groups.
3) Approve / Keep Separate / Merge.
4) Click **Export Audit** to download the tamper-evident log.

## Stop
`Ctrl+C` then `docker compose down`

## Structure
- `backend/` FastAPI service (SQLite, SQLAlchemy, audit hash chain, dedupe pipeline)
- `frontend/` React (Vite) reviewer
- `docker-compose.yml` brings it all up.
