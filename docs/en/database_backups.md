# Database Backups

[Русский](../database_backups.md) | English

[README](../../README.en.md) | [Maintenance](deployment.md)

## Preparing a User Database Snapshot for Backup

While the bot is running, the database is copied daily at **03:00 for TG and 03:05 for VK**, using the container's Moscow time zone. The default server-side file is `data/bot_db.sqlite_backup`. It is overwritten each time: this is one local copy, not a backup history. Check the Compose logs for success or errors.

Make sure to save separate TG and VK copies **outside the servers** once a month. You will need them if a server-side copy is unavailable or corrupted. Changes made after the backup will be lost during recovery; export copies more often if that is unacceptable.

## Manual Download

Substitute the SSH addresses for your separate TG and VK instances:

| Bot | Connection |
| --- | --- |
| TG | `ssh USER@TG_HOST` |
| VK | `ssh USER@VK_HOST` |

Check the Compose logs to confirm that the nightly backup succeeded. Do not download the file while it is being overwritten.

1. Once a month, download the database backup from each server. Run the command **on your own computer, outside the SSH session**. Replace `USER@HOST` and `/path/to/project` with your SSH connection details and project directory. This command saves the copy to your Desktop; enter the corresponding server's password if prompted:
    ```bash
    scp USER@HOST:/path/to/project/data/bot_db.sqlite_backup ~/Desktop/
    ```
2. After a successful download, the database file will appear on your Desktop. Rename it before downloading the copy from the second server: include the bot (TG or VK) and the date so that you do not overwrite the first copy.

Do not skip the monthly backup: it is the fallback for recovering a recent state of the user database if the server-side backup fails. This procedure accepts the risk of losing changes made since the last saved backup.

## Recovery

These steps restore `data/bot_db.sqlite`, including users and roles. Choose one of the two options below. Replace `USER@HOST` with your SSH connection details and `/path/to/project` with the project directory; enter the password if SSH or SCP prompts for it. If a command fails, do not proceed to the next step.

The server-side backup is named `bot_db.sqlite_backup`; the code defines this name. The temporary restore file is `bot_db_restore.sqlite`, and the saved damaged database is `bot_db_broken.sqlite`. Before replacing the database, the commands use Python from the bot image to check SQLite integrity and the presence of user and role tables.

### When the Server-Side Backup Is Suitable

Use this option if `data/bot_db.sqlite_backup` still exists and contains the required state from before the failure.

1. **Connect to the server and stop the bot:**

   ```bash
   ssh USER@HOST
   cd /path/to/project
   docker compose stop school-routine-bot
   docker compose ps -a
   ```

   The expected status is `Exited`. Run the following commands in the same SSH session.

2. **Save the damaged database separately and replace it with the server-side backup.** The current file is renamed to `bot_db_broken.sqlite` and moved with its SQLite sidecar files into a new `data/damaged-DATE-TIME` directory. If the database file is already missing, the commands install the backup in its place. The original backup is preserved:

   ```bash
   (
       set -e
       cp data/bot_db.sqlite_backup data/bot_db_restore.sqlite
       test -s data/bot_db_restore.sqlite
       docker compose run --rm --no-deps -T --entrypoint python school-routine-bot - <<'PY'
   import sqlite3
   from contextlib import closing
   with closing(sqlite3.connect("file:/app/data/bot_db_restore.sqlite?mode=ro&immutable=1", uri=True)) as db:
       if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
           raise SystemExit("The backup is corrupted; replacement cancelled")
       for table in ("users", "admins", "late_catchers"):
           db.execute(f"SELECT * FROM {table} LIMIT 0")
   PY
       restore_archive="data/damaged-$(date +%Y%m%d-%H%M%S)"
       mkdir "$restore_archive"
       if [ -f data/bot_db.sqlite ]; then
           mv data/bot_db.sqlite "$restore_archive/bot_db_broken.sqlite"
       fi
       for suffix in -wal -shm -journal; do
           if [ -f "data/bot_db.sqlite$suffix" ]; then
               mv "data/bot_db.sqlite$suffix" "$restore_archive/bot_db_broken.sqlite$suffix"
           fi
       done
       test ! -e data/bot_db.sqlite
       chmod 600 data/bot_db_restore.sqlite
       mv data/bot_db_restore.sqlite data/bot_db.sqlite
   )
   ```

3. **Start the bot and verify the recovery:**

   ```bash
   docker compose up -d --no-build school-routine-bot
   docker compose ps -a
   docker compose logs --tail 100 school-routine-bot
   ```

   The expected status is `Up`. Check user details, access through `/admin` in TG or `admin` in VK, and the morning duty staff list. If the required data has not been restored or the database causes errors, proceed to the second option.

### When the Server-Side Backup Is Not Suitable

Use this option if the server-side copy is missing, corrupted, or did not resolve the problem. You need the latest valid copy previously saved **on your computer or another device outside the server**, specifically for this bot (TG or VK) and compatible with the installed version.

1. **Connect to the server and stop the bot, even if you restarted it after the first attempt:**

   ```bash
   ssh USER@HOST
   cd /path/to/project
   docker compose stop school-routine-bot
   docker compose ps -a
   ```

   The expected status is `Exited`. If the SSH session is already open, start with the `cd` command.

2. **On the device holding the backup, open a separate terminal outside the SSH session.** As described above, the filename should include the bot and date, for example `bot_db_tg_2026-10-29.sqlite_backup` or `bot_db_vk_2026-10-29.sqlite_backup`. The example below uses a TG backup on the Desktop; replace the filename, date, directory, and host with your own:

   ```bash
   scp "$HOME/Desktop/bot_db_tg_2026-10-29.sqlite_backup" USER@HOST:/path/to/project/data/bot_db_restore.sqlite
   ```

   Continue only after a successful upload. If `scp` fails, do not use a leftover temporary file.

3. **Return to the SSH session, check the uploaded backup, and replace the database.** The current file is renamed to `bot_db_broken.sqlite` and moved with its SQLite sidecar files into a new dated directory. The archive from the first attempt is preserved:

   ```bash
   (
       set -e
       test -s data/bot_db_restore.sqlite
       docker compose run --rm --no-deps -T --entrypoint python school-routine-bot - <<'PY'
   import sqlite3
   from contextlib import closing
   with closing(sqlite3.connect("file:/app/data/bot_db_restore.sqlite?mode=ro&immutable=1", uri=True)) as db:
       if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
           raise SystemExit("The backup is corrupted; replacement cancelled")
       for table in ("users", "admins", "late_catchers"):
           db.execute(f"SELECT * FROM {table} LIMIT 0")
   PY
       restore_archive="data/damaged-$(date +%Y%m%d-%H%M%S)"
       mkdir "$restore_archive"
       if [ -f data/bot_db.sqlite ]; then
           mv data/bot_db.sqlite "$restore_archive/bot_db_broken.sqlite"
       fi
       for suffix in -wal -shm -journal; do
           if [ -f "data/bot_db.sqlite$suffix" ]; then
               mv "data/bot_db.sqlite$suffix" "$restore_archive/bot_db_broken.sqlite$suffix"
           fi
       done
       test ! -e data/bot_db.sqlite
       chmod 600 data/bot_db_restore.sqlite
       mv data/bot_db_restore.sqlite data/bot_db.sqlite
   )
   ```

4. **Start the bot and verify the recovery:**

   ```bash
   docker compose up -d --no-build school-routine-bot
   docker compose ps -a
   docker compose logs --tail 100 school-routine-bot
   ```

   The expected status is `Up`. Check user details, access through `/admin` in TG or `admin` in VK, and the morning duty staff list. Contact a developer if recovery has not resolved the problem.

The database returns to the state captured in the backup; later changes to users and roles will be lost. `sent_reminders.json` is stored separately and is not restored by these commands. Recovery may cause late-arrival records to be exported again; the responsible person must check Google Sheets for duplicates.
