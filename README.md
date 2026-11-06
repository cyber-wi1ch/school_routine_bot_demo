# School Routine Bot

Бот для школьных дежурств в Telegram и ВКонтакте: читает расписание из Google Sheets, отправляет напоминания и помогает учитывать опоздания.

## С чего начать

- [Пользоваться ботом и назначать дежурных](docs/user_guide.md).
- [Назначить или сменить администратора](docs/admin_management.md).
- [Заполнить таблицы](docs/google_sheets_format.md).
- [Перезапустить или обновить через Docker Compose](docs/deployment.md).
- [Сохранить базу](docs/database_backups.md).
- [Работать над кодом](docs/good_to_know_for_developers.md).

## Локальная установка

Нужны Python 3.12–3.x и Poetry 2.x. Используйте только тестовые токены и Google-таблицы.

```bash
poetry install
```

Создайте `.env` из `.env.example`, заполните настройки, положите собственный ключ Google в `credentials_for_tables.json` и создайте каталог `data`. Создайте `school_routine_bot/admin_base_1.json` по [примеру](school_routine_bot/examples/admin_1_example.json); для теста без получателей запишите `[]`. Инструкции по получению токенов: [Telegram](docs/telegram_bot_setup.md) и [ВК](docs/vk_bot_setup.md).

```bash
poetry run python -m school_routine_bot
```

## Первый запуск через Docker Compose

Команды выполняются на сервере. Нужны Git и Docker с командой `docker compose`. Python и Poetry устанавливаются внутри образа. Используйте собственные тестовые токены и Google-таблицы.

```bash
git clone https://github.com/cyber-wi1ch/school_routine_bot_demo.git
cd school_routine_bot_demo
```

1. Если `.env` ещё нет, выполните `cp .env.example .env`. Существующие настройки не перезаписывайте.
2. Подготовьте [таблицы](docs/google_sheets_format.md), [ключ Google](docs/how_to_get_API_access_to_google_sheets.md) и заполните `.env` по инструкции для своего бота: [Telegram](docs/telegram_bot_setup.md) или [ВК](docs/vk_bot_setup.md). В ней указаны требования к обоим полям токенов; `messenger_tag` задайте как `tg` или `vk`.
3. Сохраните ключ как `credentials_for_tables.json`. Оставьте `credentials_for_tables_file="credentials_for_tables.json"`; для базы используйте значение по умолчанию или `sqlite:////app/data/bot_db.sqlite` — путь внутри контейнера.
4. Создайте `school_routine_bot/admin_base_1.json` по [примеру](school_routine_bot/examples/admin_1_example.json) и настройте [получателей уведомлений](docs/admin_management.md#сменить-получателя-служебных-уведомлений-администраторы-второго-порядка---отвественные-за-пустые-слоты-и-новых-для-тг-версии-юзеров). Для теста без получателей используйте `[]`.
5. Подготовьте файлы, которые подключает Compose, не перезаписывая существующие:

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

В демо `school_routine_bot/admin_base_1.json` подключается к контейнеру отдельно и не попадает в образ. Пользователи хранятся в SQLite; файл `user_base.json` для Compose демоверсии не нужен.

В .env нужны оба поля токенов. Даже ВК-версия требует bot_token корректного формата. Если ВК не используется, укажите vk_bot_token="unused". Для отправки сообщений нужен действующий токен соответствующего бота.

После успешной подготовки:

```bash
docker compose up -d --build school-routine-bot
docker compose ps
docker compose logs -f school-routine-bot
```

В выводе `docker compose ps` у сервиса `school-routine-bot` в колонке `STATUS` должно быть `Up` — контейнер запущен. Если строки нет или статус другой, проверьте `docker compose ps -a` и логи.

На тестовом боте зарегистрируйтесь, добавьте в таблицу дежурство с тем же ФИО на будущее время до 17:00 завтра. Через пару минут оно должно появиться в «Ближайших дежурствах». Права администратора выдаются после регистрации — [инструкция](docs/admin_management.md).

Токены, ключи и рабочую базу не добавляйте в Git.
