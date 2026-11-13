# Developer Guide

[Русский](../good_to_know_for_developers.md) | English

[README](../../README.en.md) | [Docker Compose](deployment.md)

## Local Development

Requires macOS/Linux, Python 3.12-3.x (3.13 in Docker), and Poetry 2.x. On Windows, use WSL or Docker: backups depend on the Unix-only `fcntl` module. Prepare test tokens, spreadsheets, and `.env` as described in the README; do not use production data.

For local runs, do not set `database` in `.env`: the bot uses `data/bot_db.sqlite` inside the project directory. The `/app/data` path from the README is intended for Docker.

```bash
poetry install
poetry run python -m school_routine_bot
```

This runs the bot in a terminal for development; stop it with `Ctrl+C`. Scheduling uses the system's local time. Use the `Europe/Moscow` time zone to match the server. On a server, use Docker Compose and do not run a second instance of the same bot.

## Checks

```bash
poetry run pre-commit install -t=pre-commit -t=pre-push
poetry run pre-commit run -a
poetry run pytest tests
```

Some hooks modify files; review the diff. The pytest hook runs before a push.

## Code Map

Inside `school_routine_bot/`: `settings.py` contains configuration; `main_tg.py` and `vk_bot/main_vk.py` handle startup and background tasks; messenger clients implement conversations; `google_sheets_*` handle spreadsheets; `db_files/` contains database code; and `sqlite_backup.py` handles backups.

In the demo, the package version is set statically in `pyproject.toml`; no dynamic versioning plugin is needed for local installation.

Run scripts in `migrations/` only against the appropriate schema version and after taking a backup.
