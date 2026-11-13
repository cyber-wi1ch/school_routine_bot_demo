# Assigning and Replacing Administrators

[Русский](../admin_management.md) | English

[README](../../README.en.md) | [Docker Compose commands](deployment.md)

This guide is for technical staff. Administrators manage access to late-arrival recording through `/admin` or `admin`. Service notification recipients are configured separately and may be different people.

## Assign a Main Administrator in Telegram and VK

1. Ask the user to register with both bots.
2. Find their numeric IDs in each bot's `users` table: the `telegram_id` field holds the Telegram ID, and `vk_id` holds the VK ID. These are not `@username` values or the bot's ID.
3. Telegram: on the TG server, add the user's numeric Telegram ID to the `admins` list in `.env`, keeping the existing administrators. Apply the settings through Docker Compose.
4. VK: technical staff use a one-off Python script in the VK bot container to find the user by `vk_id` and add their internal `users.id` to the `admins` table. No restart is needed.
5. On the TG server only, apply the `.env` changes from the project directory:

```bash
docker compose up -d --no-build school-routine-bot
```

Ask the new administrator to send `/admin` in Telegram and/or `admin` in VK and check that the menu opens. This hidden command is available only to main administrators.

## Replace a Main Administrator or Revoke Access

The main administrator role is stored in the `admins` table. Its `id` is the internal `users.id`, not a Telegram ID or VK ID. The bot has no command for revoking this role. The script below removes the role while keeping the user record in `users`.

1. If you are replacing an administrator, first assign the new administrator and check their access.
2. Remove the previous administrator's Telegram ID from `admins` in `.env`, keeping the other IDs. If the list is empty, explicitly set `admins=[]`: removing the setting entirely restores the default list from `settings.py`. This step is not required for a VK-only user.
3. If you changed `.env`, apply the settings from the project directory:

```bash
docker compose up -d --no-build school-routine-bot
```

4. On the corresponding bot's server, run the following script from the project directory. Replace `<USER_ID>` inside the quotes with the user's numeric ID in the relevant messenger: their Telegram ID on the TG server or their VK ID on the VK server.

```bash
docker compose exec -T school-routine-bot .venv/bin/python - <<'PY'
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from school_routine_bot.db_files.db_models import Admin, User
from school_routine_bot.settings import get_settings

MESSENGER_ID = int("<USER_ID>")

settings = get_settings()
id_field = User.chat_id if settings.messenger_tag == "tg" else User.vk_id
engine = create_engine(settings.database)

with Session(engine) as session:
    user = (
        session.query(User)
        .filter(id_field == MESSENGER_ID)
        .one_or_none()
    )
    if user is None:
        raise SystemExit("User not found. Check the ID and server.")

    # Both bots assign administrators by Telegram ID at startup.
    if user.chat_id is not None and user.chat_id in settings.admins:
        raise SystemExit(
            "First remove the Telegram ID from admins in .env "
            "and apply the settings with docker compose up."
        )

    admin = session.get(Admin, user.id)
    if admin is None:
        print("The user no longer has the main administrator role.")
    else:
        session.delete(admin)
        session.commit()
        print("Main administrator role revoked. User record preserved.")

engine.dispose()
PY
```

The script selects the ID field using the current container's `messenger_tag` setting. Run it separately on the corresponding TG and VK servers.

**Deleting only the database record is not enough:** if the Telegram ID remains in the settings, the bot will grant the role again at its next startup. No additional restart is needed after running the script because permission checks read the database. The script does not change the morning duty role or the service notification recipient list.

## VK-Specific Behavior

The current deployment uses separate TG and VK databases. The `admins` list in `.env` is processed as Telegram IDs, even in the VK version. For a VK-only user, a developer grants or revokes access directly in the VK database. Registration or role changes on the TG server do not transfer these permissions.

## Change Service Notification Recipients

These are a separate group of administrators responsible for notifications about unfilled duty slots and people who are not registered with the TG bot.

In `school_routine_bot/admin_base_1.json`, replace the relevant recipient's record while keeping the others. In the template below, replace `<RECIPIENT_ID>` with their numeric ID, without quotes or angle brackets:

```text
[{"admin_id": <RECIPIENT_ID>, "name": "Иван", "by_father_name": "Иванович"}]
```

Use the ID for the corresponding messenger and ask the recipient to allow messages from the bot. Use `[]` to test without recipients. In the demo, this file is mounted from the host; restart the service after changing it:

```bash
docker compose restart school-routine-bot
```

These recipients serve a different purpose: at 13:00, they receive information in the TG version about unfilled slots and people who are not TG bot users. When handing over responsibilities, check both administrator permissions and the recipient list. This list does not grant access to `/admin` in Telegram or `admin` in VK. That hidden command is available only to main administrators and lets them manage the morning duty staff list.
