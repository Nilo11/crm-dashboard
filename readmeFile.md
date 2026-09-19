# AGENTSReadmeFile.md

## Project overview

This repo is a small Flask + pywebview CRM dashboard. The app serves a web UI from [static/index.html](static/index.html) and exposes JSON APIs from [app.py](app.py). Data is stored in SQLite at runtime in the workspace file `crm_database.db`.

Primary entry points:
- [app.py](app.py) — Flask app, DB setup, API routes, and pywebview window bootstrap
- [static/index.html](static/index.html) — frontend UI and client-side API calls
- [schema.sql](schema.sql) — schema reference, but not a direct source of truth for the runtime SQLite database
- [ReadMe.md](ReadMe.md) — repo notes and quick-start guidance

## Working conventions

- Treat [app.py](app.py) as the source of truth for the runtime database schema and migrations.
- The database is initialized in `init_db()`. If a schema change is needed, update both the `CREATE TABLE` logic and the migration logic that checks for missing columns.
- `schema.sql` contains MySQL-style DDL and may not match SQLite exactly; do not assume it is safe to copy directly into the live DB.
- Frontend and backend are tightly coupled. UI changes often require matching API or data expectations in [static/index.html](static/index.html).
- The app creates a desktop window with pywebview and serves the browser at `http://127.0.0.1:5000`.

## Run and validation commands

Use the project venv when running the app locally:

- PowerShell: `./.venv-1/Scripts/python.exe app.py`
- Or activate venv first: `.venv-1\Scripts\Activate.ps1` then `python app.py`

Useful checks:
- `./.venv-1/Scripts/python.exe scripts/test_post.py` exercises the `/api/leads` POST flow
- If a DB change is needed, stop the app, delete `crm_database.db`, and restart so `init_db()` can recreate seed data

## Common pitfalls

- Do not duplicate the same route definition twice. The file currently contains repeated `DELETE` and `export` route blocks; keep additions clean and avoid copy-paste duplication.
- Phone validation uses `phonenumbers`; invalid or empty values should be handled consistently in both create and update flows.
- Email uniqueness is enforced in SQLite via `UNIQUE` on the `email` column.
- Existing seeded records are created in `init_db()`; if you change seed content or schema, verify the startup flow still works with the existing DB file.

## When editing code

- Prefer minimal, direct changes in [app.py](app.py) for API behavior.
- If UI logic changes, update both the HTML and any matching route/response contract.
- Log unexpected exceptions to `error.log` rather than leaving silent failures.
- Keep API responses consistent with the existing JSON shape and HTTP status codes.

## References

- [ReadMe.md](ReadMe.md)
- [app.py](app.py)
- [static/index.html](static/index.html)
- [schema.sql](schema.sql)
- [requirements.txt](requirements.txt)
