# School Routine Bot

[Русский](README.md) | English

A school duty bot for Telegram and VK: reads schedules from Google Sheets, sends reminders, and helps record late arrivals.

The bot interface and worksheet names remain in Russian. This documentation keeps their exact labels where needed.

## Getting Started

- [Use the bot and assign morning duty staff](docs/en/user_guide.md).
- [Assign or replace an administrator](docs/en/admin_management.md).
- [Prepare the spreadsheets](docs/en/google_sheets_format.md).
- [Restart or update with Docker Compose](docs/en/deployment.md).
- [Back up the database](docs/en/database_backups.md).
- [Work on the code](docs/en/good_to_know_for_developers.md).

## Local Installation

Requires Python 3.12-3.x and Poetry 2.x. Use test tokens and test Google spreadsheets only.

```bash
poetry install
```

Create `.env` from `.env.example`, fill in the settings, place your own Google service account key in `credentials_for_tables.json`, and create the `data` directory. Create `school_routine_bot/admin_base_1.json` using the [example](school_routine_bot/examples/admin_1_example.json); use `[]` to test without notification recipients. Token setup instructions: [Telegram](docs/en/telegram_bot_setup.md) and [VK](docs/en/vk_bot_setup.md).

```bash
poetry run python -m school_routine_bot
```

## First Start with Docker Compose

Run these commands on the server. Git and Docker with the `docker compose` command are required. Python and Poetry are installed inside the image. Use your own test tokens and test Google spreadsheets.

```bash
git clone https://github.com/cyber-wi1ch/school_routine_bot_demo.git
cd school_routine_bot_demo
```

1. If `.env` does not exist, run `cp .env.example .env`. Do not overwrite existing settings.
2. Prepare the [spreadsheets](docs/en/google_sheets_format.md) and [Google key](docs/en/how_to_get_API_access_to_google_sheets.md), then fill in `.env` using the instructions for [Telegram](docs/en/telegram_bot_setup.md) or [VK](docs/en/vk_bot_setup.md). These explain the requirements for both token fields. Set `messenger_tag` to `tg` or `vk`.
3. Save the key as `credentials_for_tables.json`. Keep `credentials_for_tables_file="credentials_for_tables.json"`; use the default database setting or `sqlite:////app/data/bot_db.sqlite`, which is the path inside the container.
4. Create `school_routine_bot/admin_base_1.json` using the [example](school_routine_bot/examples/admin_1_example.json) and configure [notification recipients](docs/en/admin_management.md#change-service-notification-recipients). Use `[]` to test without recipients.
5. Prepare the files mounted by Compose without overwriting existing files:

```bash
(
    set -eu
    mkdir -p data
    if [ ! -e sent_reminders.json ]; then printf '{}\n' > sent_reminders.json; fi
    test -f sent_reminders.json
    test -f .env
    test -f credentials_for_tables.json
    test -f school_routine_bot/admin_base_1.json
)
```

In the demo, `school_routine_bot/admin_base_1.json` is mounted separately and is not included in the image. Users are stored in SQLite; the demo's Compose setup does not need `user_base.json`.

Both token fields are required in `.env`. Even the VK version requires a correctly formatted `bot_token`. If VK is not used, set `vk_bot_token="unused"`. Sending messages requires a valid token for the corresponding bot.

Once preparation succeeds:

```bash
docker compose up -d --build school-routine-bot
docker compose ps
docker compose logs -f school-routine-bot
```

In the output of `docker compose ps`, the `school-routine-bot` service should have `Up` in the `STATUS` column. If the row is missing or the status differs, check `docker compose ps -a` and the logs.

Register with the test bot and add a duty to the spreadsheet using the same full name, with a future start time before 17:00 tomorrow. It should appear under "Ближайшие дежурства" (Upcoming duties) within a few minutes. Administrator permissions are granted after registration; see the [instructions](docs/en/admin_management.md).

Do not commit tokens, keys, or the production database.
