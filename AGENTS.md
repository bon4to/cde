# Repository Guidelines

## Project Structure & Module Organization

CDE is a Flask-based operations app for inventory, dispatch, and lightweight ERP workflows. The main route surface lives in `cde.py`; `cde_wsgi.py` runs the Waitress entry point. Reusable application logic is under `app/models/`, service code is in `app/services/`, and Flask configuration helpers are in `app/utils/`. Jinja2 pages and shared components live in `templates/`, static CSS/JS/images/fonts/SVGs live in `static/`, SQL query templates live in `db/queries/`, migrations live in `db/migrations/`, and tests live in `tests/`.

## Build, Test, and Development Commands

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the debug server on port `5100`:

```bash
python cde.py
```

Run the production-style Waitress server on port `5005`:

```bash
python cde_wsgi.py
```

Run the test suite:

```bash
pytest
pytest --cov=app --cov=cde
```

Create a timestamped migration stub:

```bash
python scripts/create_migration.py add_example_table
```

## Coding Style & Naming Conventions

Use Python 3 with 4-space indentation. Follow the existing module style: helper modules use names like `dbUtils.py`, `estoqueUtils.py`, and `stickerUtils.py`; tests use `test_<module>.py`. Keep domain terms in Portuguese when matching the current UI and business language (`estoque`, `cargas`, `envase`, `processamento`). Jinja templates use `.j2`; group page templates by feature under `templates/pages/`.

## Testing Guidelines

Tests use `pytest`, with some `unittest` classes where already present. Put fixtures in `tests/conftest.py`, prefer temporary files/databases for filesystem or SQLite behavior, and freeze time for date-sensitive cases with `freezegun`. Name tests by behavior, for example `test_run_pending_migrations` or `test_valid_date_with_cs_lote`.

## Commit & Pull Request Guidelines

This workspace has no Git metadata, so local commit history could not be inspected. Use concise conventional commits such as `fix: handle empty query file` or `feat: add migration status page`. Pull requests should include a short problem summary, implementation notes, test results, linked issues when available, and screenshots for UI/template changes.

## Security & Configuration Tips

Copy `.env.example` to `.env` locally and never commit secrets. Required settings include `SECRET_KEY`, database paths, ODBC/API credentials, and optional Telegram tokens. The ERP ODBC flow depends on the companion `cde-api` service being available where the driver is installed.
