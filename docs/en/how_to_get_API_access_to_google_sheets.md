# Google Sheets Access

[Русский](../how_to_get_API_access_to_google_sheets.md) | English

[README](../../README.en.md) | [Spreadsheet format](google_sheets_format.md)

The bot uses a Google service account JSON key. OAuth sign-in and running `quickstart.py` are not required.

## Create a Key and Grant Access

1. In [Google Cloud Console](https://console.cloud.google.com/), create or select a project. Under **APIs & Services > Library**, enable **Google Sheets API** and **Google Drive API**, as described in the [gspread documentation](https://docs.gspread.org/en/master/oauth2.html#enable-api-access-for-a-project).
2. Open **IAM & Admin > Service Accounts > Create service account** and name the account. You can skip assigning project roles: spreadsheet access is granted separately in step 5. See [Create service accounts](https://docs.cloud.google.com/iam/docs/service-accounts-create).
3. Open the new account and select **Keys > Add key > Create new key > JSON > Create**. The browser downloads a JSON file. See [Create service account keys](https://docs.cloud.google.com/iam/docs/keys-create-delete).
4. Save it as `credentials_for_tables.json` in the project root. In `.env`, set `credentials_for_tables_file="credentials_for_tables.json"`.
5. Find `client_email` in the JSON file. Open each spreadsheet's sharing settings and add that address: grant **Viewer** access to the duty schedule and **Editor** access to morning duties. If both use one spreadsheet, grant **Editor** access.
6. Fill in `table_url` and `morning_duty_table_url` in `.env`. Prepare the worksheets using the [format specification](google_sheets_format.md), then continue with the [first start](../../README.en.md#first-start-with-docker-compose).

Your personal account's access does not grant access to the service account. If the school's Workspace policy prevents adding the address, contact its administrator.

## Troubleshooting

| Error | What to check |
| --- | --- |
| Google Cloud does not allow key creation | Your account permissions and the organization policy; contact the Google Cloud administrator |
| `FileNotFoundError` | The `credentials_for_tables_file` path to the JSON key |
| `SpreadsheetNotFound` / access denied | The spreadsheet URL and access granted to `client_email` |
| `WorksheetNotFound` | The exact worksheet name |
| Cannot write data | Editor access to the morning duty spreadsheet |

Do not publish the key. Test write access on a test spreadsheet.
