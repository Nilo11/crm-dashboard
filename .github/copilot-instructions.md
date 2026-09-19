# Copilot instructions for this repo

## Scope

This repository is a small Flask CRM dashboard with a local SQLite database and a pywebview desktop shell. Keep changes small and aligned with the existing app structure.

## Key files

- [app.py](../app.py) — backend API and database initialization
- [static/index.html](../static/index.html) — frontend UI and client calls
- [schema.sql](../schema.sql) — schema reference only; not the authoritative runtime schema
- [ReadMe.md](../ReadMe.md) — project notes and startup guidance

## Working rules

- Treat [app.py](../app.py) as the primary implementation file for API and DB behavior.
- Preserve the SQLite-first runtime behavior; do not assume MySQL DDL in [schema.sql](../schema.sql) is directly valid for the live DB.
- If you add or change a database column, update the migration logic in `init_db()` as well as the `CREATE TABLE` definition.
- Keep the API contract and the frontend UI in sync when changing fields or payloads.
- Prefer existing route and response patterns over introducing a new architecture.
- Validate with the project venv and the repo’s lightweight API smoke script when possible.

## Quick commands

- Run app: `./.venv-1/Scripts/python.exe app.py`
- Smoke test: `./.venv-1/Scripts/python.exe scripts/test_post.py`

## Common pitfalls

- Empty or invalid phone numbers should be handled consistently; the app validates them via the `phonenumbers` library.
- Email uniqueness is enforced in SQLite and should stay consistent with the schema.
- Recreating the DB file is sometimes necessary after schema changes because the app reuses `crm_database.db` at runtime.
