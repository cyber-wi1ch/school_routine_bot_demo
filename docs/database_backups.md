# Резервные копии базы

Русский | [English](en/database_backups.md)

[README](../README.md) · [Обслуживание](deployment.md)

## Подготовка слепка базы данных пользователей для бэкапа

При работающем боте база копируется ежедневно: **TG — в 03:00, VK — в 03:05** по времени контейнера (Москва). По умолчанию файл на сервере — `data/bot_db.sqlite_backup`. Он перезаписывается: это одна локальная копия, а не архив. Успех или ошибку смотрите в логах Compose.

! Раз в месяц обязательно сохраняйте отдельные копии TG и VK **вне серверов**. Они понадобятся, если серверная копия недоступна или повреждена. Более поздние изменения при восстановлении будут потеряны; если это неприемлемо, выгружайте копии чаще.

## Ручная копия

Для отдельных экземпляров TG и VK подставьте свои SSH-адреса:

| Бот | Подключение |
| --- | --- |
| TG | `ssh USER@TG_HOST` |
| VK | `ssh USER@VK_HOST` |

Убедитесь по логам Compose, что ночной бэкап завершился успешно. Не скачивайте файл во время его перезаписи.

1. Раз в месяц сохраняйте бэкап базы данных с каждого сервера. Выполняйте команду **на своём компьютере, вне SSH-сеанса**. Замените `USER@HOST` и `/path/to/project` на свои SSH-данные и каталог проекта. Следующая команда сохраняет копию на рабочий стол; по запросу введите пароль от нужного сервера:
    ```bash
    scp USER@HOST:/path/to/project/data/bot_db.sqlite_backup ~/Desktop/
    ```
2. После успешного скачивания на рабочем столе появится файл базы данных. Переименуйте его до загрузки копии со второго сервера: укажите в названии бота (TG или VK) и дату, чтобы не перезаписать первую копию.

Не игнорируйте ежемесячный бэкап, так как это единственный способ восстановить ближайшее состояние базы данных пользователей в случае каких-то поломок серверного бэкап-файла бд. (утерю новых данных с момента последнего бэкапирования до следующего принимаем как приемлемый риск.)
## Восстановление

Восстанавливается база `data/bot_db.sqlite`, включая пользователей и роли. Выберите один из двух вариантов ниже. Подставьте вместо `USER@HOST` свои SSH-данные и замените `/path/to/project` на каталог проекта; по запросу SSH или SCP введите пароль. При ошибке команды не переходите к следующему шагу.

Серверный бэкап называется `bot_db.sqlite_backup` — это имя задаёт код. Для временного файла используется `bot_db_restore.sqlite`, для сохранённого повреждённого — `bot_db_broken.sqlite`. Перед заменой команды проверяют целостность SQLite и наличие таблиц пользователей и ролей через Python из образа бота.

### Если подходит серверный бэкап

Используйте этот вариант, если `data/bot_db.sqlite_backup` сохранился и содержит нужное состояние до поломки.

1. **Подключитесь к серверу и остановите бота:**

   ```bash
   ssh USER@HOST
   cd /path/to/project
   docker compose stop school-routine-bot
   docker compose ps -a
   ```

   Ожидаемый статус — `Exited`. Дальнейшие команды выполняйте в этом же SSH-сеансе.

2. **Сохраните повреждённую базу отдельно и замените её серверной копией.** Текущий файл будет переименован в `bot_db_broken.sqlite` и перенесён со служебными файлами SQLite в новую папку `data/damaged-ДАТА-ВРЕМЯ`. Если рабочий файл уже отсутствует, команды установят копию на его место. Исходный бэкап сохранится:

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
           raise SystemExit("Копия повреждена; замена отменена")
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

3. **Запустите бота и проверьте восстановление:**

   ```bash
   docker compose up -d --no-build school-routine-bot
   docker compose ps -a
   docker compose logs --tail 100 school-routine-bot
   ```

   Ожидаемый статус — `Up`. Проверьте данные пользователя, доступ через `/admin` в TG или `admin` в ВК и список дежурных по опозданиям. Если нужные данные не восстановились или база вызывает ошибки, перейдите ко второму варианту.

### Если серверный бэкап не подходит

Используйте этот вариант, если серверной копии нет, она повреждена или восстановление из неё не помогло. Нужна последняя исправная копия, ранее выгруженная **на ваш компьютер или другое устройство вне сервера**, именно для этого бота (TG или ВК) и совместимая с установленной версией.

1. **Подключитесь к серверу и остановите бота, даже если уже запускали его после первой попытки:**

   ```bash
   ssh USER@HOST
   cd /path/to/project
   docker compose stop school-routine-bot
   docker compose ps -a
   ```

   Ожидаемый статус — `Exited`. Если SSH-сеанс уже открыт, выполняйте команды начиная с `cd`.

2. **На устройстве с сохранённой копией откройте отдельный терминал, вне SSH-сеанса.** Как указано выше, имя копии должно содержать бота и дату: например, `bot_db_tg_2026-10-29.sqlite_backup` или `bot_db_vk_2026-10-29.sqlite_backup`. Ниже пример для TG и файла на рабочем столе — замените имя, дату, папку и IP на свои:

   ```bash
   scp "$HOME/Desktop/bot_db_tg_2026-10-29.sqlite_backup" USER@HOST:/path/to/project/data/bot_db_restore.sqlite
   ```

   Продолжайте только после успешной загрузки. При ошибке `scp` не используйте оставшийся временный файл.

3. **Вернитесь в SSH-сеанс. Проверьте загруженную копию и замените базу.** Текущий файл будет переименован в `bot_db_broken.sqlite` и перенесён со служебными файлами SQLite в новую папку с датой. Архив первой попытки сохранится:

   ```bash
   (
       set -e
       test -s data/bot_db_restore.sqlite
       docker compose run --rm --no-deps -T --entrypoint python school-routine-bot - <<'PY'
   import sqlite3
   from contextlib import closing
   with closing(sqlite3.connect("file:/app/data/bot_db_restore.sqlite?mode=ro&immutable=1", uri=True)) as db:
       if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
           raise SystemExit("Копия повреждена; замена отменена")
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

4. **Запустите бота и проверьте восстановление:**

   ```bash
   docker compose up -d --no-build school-routine-bot
   docker compose ps -a
   docker compose logs --tail 100 school-routine-bot
   ```

   Ожидаемый статус — `Up`. Проверьте данные пользователя, доступ через `/admin` в TG или `admin` в ВК и список дежурных по опозданиям. Если восстановление не помогло, обратитесь к разработчику.

База вернётся к состоянию на дату копии; более поздние изменения пользователей и ролей будут потеряны. Файл `sent_reminders.json` хранится отдельно и этими командами не восстанавливается. После восстановления возможна повторная выгрузка опозданий — ответственный должен сверить Google Sheets.
