# Для разработчиков

[README](../README.md) · [Docker Compose](deployment.md)

## Локальная разработка

Нужны macOS/Linux, Python 3.12–3.x (в Docker — 3.13) и Poetry 2.x. На Windows используйте WSL или Docker: резервирование зависит от Unix-модуля `fcntl`. Подготовьте тестовые токены, таблицы и `.env` по README; рабочие данные не используйте.

Для локального запуска не задавайте `database` в `.env`: бот использует базу `data/bot_db.sqlite` в папке проекта. Путь `/app/data` из README предназначен для Docker.

```bash
poetry install
poetry run python -m school_routine_bot
```

Это запуск в терминале для разработки, остановка — `Ctrl+C`. Расписание использует местное время системы; для совпадения с сервером нужен часовой пояс `Europe/Moscow`. На сервере используйте Docker Compose и не запускайте второй экземпляр того же бота.

## Проверки

```bash
poetry run pre-commit install -t=pre-commit -t=pre-push
poetry run pre-commit run -a
poetry run pytest tests
```

Некоторые хуки исправляют файлы — просмотрите diff. Хук pytest выполняется перед push.

## Где искать код

В `school_routine_bot/`: `settings.py` — настройки; `main_tg.py` и `vk_bot/main_vk.py` — запуск и фоновые задачи; клиенты мессенджеров — диалоги; `google_sheets_*` — таблицы; `db_files/` — база; `sqlite_backup.py` — резервирование.

В демо версия пакета задаётся статически в `pyproject.toml`; плагин динамического версионирования для локальной установки не нужен.

Скрипты в `migrations/` применяйте только к подходящей версии схемы и после резервного копирования.
