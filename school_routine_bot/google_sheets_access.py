from pprint import pprint

import apiclient
import httplib2
from googleapiclient.discovery import Resource
from oauth2client.service_account import ServiceAccountCredentials

from school_routine_bot.settings import SettingsToAccessGoogleSheets

# Set the path to your service account key file
# using the credentials_for_tables_file setting
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
)  # Authorize the HTTP client used for all requests
service = apiclient.discovery.build(
    "sheets", "v4", http=httpAuth
)  # Create a client for Google Sheets API v4
# API connection is configured above
spreadsheets: Resource = service.spreadsheets()
values: Resource = spreadsheets.values()
value: Resource = values.get(range="A1:E10", spreadsheetId=spreadsheet_id)
executed = value.execute()
# Standard Google API client wrapper (see the API documentation)
pprint(values)
pprint(executed)
