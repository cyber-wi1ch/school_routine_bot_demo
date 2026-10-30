# Доступ к Google Sheets

[README](../README.md) · [Формат таблиц](google_sheets_format.md)

Бот использует JSON-ключ сервисного аккаунта Google. OAuth-вход и запуск `quickstart.py` не требуются.

## Получить ключ и открыть доступ

1. В [Google Cloud Console](https://console.cloud.google.com/) создайте или выберите проект. В **APIs & Services → Library** включите **Google Sheets API** и **Google Drive API**, как описано в [документации gspread](https://docs.gspread.org/en/master/oauth2.html#enable-api-access-for-a-project).
2. Откройте **IAM & Admin → Service Accounts → Create service account** и задайте имя аккаунта. Назначение ролей в проекте можно пропустить: доступ к таблицам выдаётся отдельно, на шаге 5. [Создание сервисного аккаунта](https://docs.cloud.google.com/iam/docs/service-accounts-create).
3. Откройте созданный аккаунт: **Keys → Add key → Create new key → JSON → Create**. Браузер скачает JSON-файл. [Создание ключа](https://docs.cloud.google.com/iam/docs/keys-create-delete).
4. Сохраните файл как `credentials_for_tables.json` в корне проекта. В `.env` укажите `credentials_for_tables_file="credentials_for_tables.json"`.
5. В JSON найдите `client_email`. В каждой Google-таблице откройте **Настройки доступа** и добавьте этот адрес: к расписанию — **Читатель**, к утренним дежурствам — **Редактор**. Для общей таблицы нужна роль **Редактор**.
6. В `.env` заполните `table_url` и `morning_duty_table_url`. Подготовьте листы по [описанию формата](google_sheets_format.md), затем продолжите [первый запуск](../README.md#первый-запуск-через-docker-compose).

Доступ вашего личного аккаунта не заменяет доступ сервисного аккаунта. Если школьный Workspace запрещает добавление адреса, обратитесь к его администратору.

## Если не получилось

| Ошибка | Что проверить |
| --- | --- |
| Google Cloud не разрешает создать ключ | Права вашей учётной записи и политику организации; обратитесь к администратору Google Cloud |
| `FileNotFoundError` | Путь `credentials_for_tables_file` к JSON-ключу |
| `SpreadsheetNotFound` / нет доступа | Ссылку и доступ для `client_email` |
| `WorksheetNotFound` | Точное название листа |
| Не удаётся записать данные | Право редактирования таблицы утренних дежурств |

Ключ не публикуйте. Проверяйте запись на тестовой таблице.
