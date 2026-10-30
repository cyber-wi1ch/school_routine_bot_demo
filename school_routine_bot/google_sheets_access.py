from pprint import pprint

import apiclient
import httplib2
from googleapiclient.discovery import Resource
from oauth2client.service_account import ServiceAccountCredentials

from school_routine_bot.settings import SettingsToAccessGoogleSheets

# Путь к файлу с ключами: Вы должны подставить свой путь к файлу,
# который мы назвали credentials.json
settings = SettingsToAccessGoogleSheets()
credentials_file = settings.credentials_for_tables_file
spreadsheet_id = settings.table_id

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    credentials_file,
    [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ],
)  # services with which we will work

httpAuth = credentials.authorize(
    httplib2.Http()
)  # Авторизуемся в системе, через этот обьект проходят все запросы
service = apiclient.discovery.build(
    "sheets", "v4", http=httpAuth
)  # Выбираем работу с таблицами и 4 версию API - обертка
# ВЫШЕ ПОДКЛЮЧЕНИЕ АПИ
spreadsheets: Resource = service.spreadsheets()
values: Resource = spreadsheets.values()
value: Resource = values.get(range="A1:E10", spreadsheetId=spreadsheet_id)
executed = value.execute()
# стандартная гугловская обертка апи (можно найти в документации)
pprint(values)
pprint(executed)
