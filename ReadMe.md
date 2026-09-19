# ReadMe.md — instructions for crm-dashboard

Purpose
- Provide minimal, actionable guidance for AI coding agents working on this repo.

Quick run (development)
- Activate the project venv (Windows example): `.venv-1\Scripts\Activate.ps1` then run `python app.py`.
- Or run directly with the venv interpreter: `.\ .venv-1\Scripts\python.exe app.py`.
- App listens on port 5000 and opens a frameless webview window.

Key files
- app.py — main Flask backend and initializer. See [app.py](app.py).
- Frontend — static files served from [static/index.html](static/index.html).
- schema.sql — reference SQL schema (note: MySQL-style DDL). See [schema.sql](schema.sql).
- SQLite DB file created at runtime: `crm_database.db` (tracked in workspace).

Important notes for agents
- The codebase uses SQLite at runtime (`crm_database.db`) while `schema.sql` contains MySQL-style DDL (AUTO_INCREMENT, ENUM). Do not assume `schema.sql` is a drop-in for the running DB — update `init_db()` in `app.py` when changing SQLite schema.
- `init_db()` in `app.py` bootstraps the `leads` table and seed data; restarting the app will recreate or reuse `crm_database.db` as-is.
- Frontend and backend are tightly coupled: UI lives in `static/` and calls `/api/*` endpoints in `app.py`. For UI work, update both `static/index.html` and the corresponding Flask route.

Common tasks and quick tips
- Add an API route: edit `app.py`, follow existing endpoint patterns, and update `static` UI if needed.
- Reset DB: stop app, delete `crm_database.db`, then restart to re-run `init_db()` seed logic.
- Export/Import: use `/api/export/csv` for CSV export; no import endpoint currently.

Recommended agent customizations (next)
- Create a `db-migrations` skill to manage schema changes (SQLite ↔ MySQL differences).
- Add a `test-runner` skill to run linting and any future tests.

Where to look for more context
- Project entry: [app.py](app.py)
- Frontend UX: [static/index.html](static/index.html)
- Schema reference: [schema.sql](schema.sql)

If you want, I can also add a `.github/copilot-instructions.md` variant or split frontend/backend instructions into separate skill files.
