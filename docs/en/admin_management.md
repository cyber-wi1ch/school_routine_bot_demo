# Assigning and Replacing Administrators

[Русский](../admin_management.md) | English

[README](../../README.en.md) | [Docker Compose commands](deployment.md)

This guide is for technical staff. Administrators manage access to late-arrival recording through `/admin` or `admin`. Service notification recipients are configured separately and may be different people.

## Assign a Main Administrator in Telegram

1. Ask the user to register with the bot.
2. Find their numeric Telegram ID in the `telegram_id` field of the `users` table. This is not their `@username` or the bot's ID.
3. Add the ID to the `admins` list in `.env`, keeping the existing administrators. For example: `admins=[123456789, 987654321]`.
4. Apply the settings from the project directory on the appropriate server:

```bash
docker compose up -d --no-build school-routine-bot
```

Ask the new administrator to send `/admin` in Telegram and check that the menu opens. This command is available only to main administrators.

## Replace a Main Administrator or Revoke Access

First assign the new administrator and check their access. Then remove the previous administrator's ID from `admins` in `.env` and apply the settings using the command above.

**This alone does not revoke access:** an assigned role remains in the database. Technical staff must also remove the previous administrator's role from the `admins` table while keeping their user record in `users`. The bot has no command for revoking this role.

## VK-Specific Behavior

The current deployment uses separate TG and VK databases. The `admins` list in `.env` is processed as Telegram IDs, even in the VK version. For a VK-only user, a developer grants or revokes access directly in the VK database. Registration or role changes on the TG server do not transfer these permissions.

## Change Service Notification Recipients

These users receive information about unfilled duty slots and assigned people who are not registered with the bot. Scheduled notifications are sent at 13:00 Moscow time through the messenger used by the corresponding bot instance.

In `school_routine_bot/admin_base_1.json`, replace the relevant recipient's record while keeping the others:

```json
[{"admin_id": 123456789, "name": "Иван", "by_father_name": "Иванович"}]
```

Use the ID for the corresponding messenger and ask the recipient to allow messages from the bot. Use `[]` to test without recipients. In the demo, this file is mounted from the host; restart the service after changing it:

```bash
docker compose restart school-routine-bot
```

This list does not grant access to `/admin` in Telegram or `admin` in VK. When handing over responsibilities, check administrator permissions and notification recipients separately.
