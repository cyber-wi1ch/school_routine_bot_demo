# Running and Maintaining the Bot with Docker Compose

[Русский](../deployment.md) | English

[README](../../README.en.md) | [Database backups](database_backups.md) | [Administrator changes](admin_management.md)

## Docker Compose

Run all commands on the relevant server from the project directory containing `docker-compose.yaml`. There is one service, `school-routine-bot`; `.env` selects the messenger. Use separate instances for TG and VK and run the commands for each server separately.

| Action | Command |
| --- | --- |
| Start / rebuild | `docker compose up -d --build school-routine-bot` |
| Restart | `docker compose restart school-routine-bot` |
| Apply `.env` changes without building | `docker compose up -d --no-build school-routine-bot` |
| Stop | `docker compose stop school-routine-bot` |
| Status | `docker compose ps -a` |
| Logs | `docker compose logs --tail 100 -f school-routine-bot` |

After startup, `docker compose ps -a` should show `Up` in the `STATUS` column for `school-routine-bot`. If the row is missing or the status differs, check the logs.

After `.env` changes, `up -d --no-build` recreates the container with the new settings and starts it in the background. `--no-build` prevents image building; this command does not create a build cache. See the [`up` reference](https://docs.docker.com/reference/cli/docker/compose/up/).

A regular [`restart`](https://docs.docker.com/reference/cli/docker/compose/restart/) does not apply new environment variables. Code changes require an image rebuild. `school_routine_bot/admin_base_1.json` is mounted from the host, so restarting the service is enough after editing it.

Pressing `Ctrl+C` while viewing logs stops the log viewer, not the bot. Do not run the same bot concurrently through Poetry, systemd, or another container.

## Updating

Before updating, save a [backup](database_backups.md). If the database schema changes, agree on the migration procedure with a developer: starting the bot does not automatically update existing columns. If a command fails, do not proceed to the next step.

1. Connect to the relevant server over SSH. Replace `USER@HOST` with your SSH connection details; enter the password if prompted:
```bash
ssh USER@HOST
```

2. Open the project directory, replacing `/path/to/project` with your path:
```bash
cd /path/to/project
```
3. Update the agreed branch:
```bash
git pull
```
4. Rebuild the project's container image:
```bash
docker compose build school-routine-bot
```
5. Once the build completes, usually indicated by `Built` with a check mark, stop the previous container:

```bash
docker compose stop school-routine-bot
```
The bot will remain unavailable until you complete the next step.

6. Start the new container:
```bash
docker compose up -d school-routine-bot
```
Compose handles replacing the old container with the new one. The bot is unavailable during this transition. The expected status is `Up`.

7. No further console output can be normal. To follow the logs in real time, run:
```bash
docker compose logs -f school-routine-bot
```
Check the logs for errors and test a bot response, such as "Ваши данные" (Your details).

The database and JSON files are mounted from the host, so recreating the container preserves them. A rollback requires compatible code and database versions.

## Data and Logs

- `data/` and `sent_reminders.json` persist on the host. The JSON key and `school_routine_bot/admin_base_1.json` are mounted read-only. Compose requires these paths to exist before startup; see the README for preparation.
- Use `docker compose logs` as the primary diagnostic tool. `/app/school_routine_bot.log` stays inside the container and is lost when the container is recreated.
- The image uses the `Europe/Moscow` time zone. Check it without starting the bot: `docker compose run --rm --no-deps --entrypoint date school-routine-bot '+%H:%M %z'`; the expected offset is `+0300`.
- See the [user guide](user_guide.md#export-to-google-sheets) for late-arrival export times and the [backup guide](database_backups.md) for nightly backups.

Remove personal data and secrets before sharing logs. The current code does not prevent duplicate exports when two processes share a database; keep the deployments separate.

## Checking Free Disk Space

When there are no updates or rebuilds, check each server monthly. Make the first follow-up check after a week to estimate disk usage growth. Check more often if usage grows quickly and before rebuilding.

After connecting over SSH, run this from any directory:

```bash
df -h /
```

`Avail` is free space; `Use%` is the proportion of the disk in use. As a guideline, if **80% or more is used, or less than 3 GB is free**, send the output to a developer for inspection and cleanup.

A developer can inspect Docker and system journal disk usage with:

```bash
docker system df
journalctl --disk-usage
```

These commands do not delete anything. Docker's cache grows during builds; even without rebuilds, logs and backups may consume more space. Base cleanup decisions on the inspection results.
