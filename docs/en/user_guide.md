# User Guide

[Русский](../user_guide.md) | English

[README](../../README.en.md) | [Spreadsheet format](google_sheets_format.md)

You need Telegram or VK. Ask the responsible person at the school for the bot link. Button labels below are kept in Russian to match the bot interface.

## Registration and Schedule

1. Send `/start` in Telegram or `Начать` (Start) in VK.
2. Enter your full name exactly as it appears in the schedule, for example `Иванов Иван Иванович`.
3. Check "Ваши данные" (Your details); if anything is incorrect, select "Исправить данные" (Edit details).

"Ближайшие дежурства" (Upcoming duties) shows duties starting between now and **17:00 tomorrow, inclusive**. After updating the schedule in Google Sheets, wait a few minutes. If an entry is missing, check the full name, date, and time.

## For Administrators

The current deployment uses separate TG and VK databases: users must register and receive roles in each bot they use.

Send `/admin` in TG or `admin` in VK, select "Добавить в дежурные по опозданиям" (Assign morning duty), and enter a registered user's full name. Check "Список дежурных по опозданиям" (Morning duty staff). The user will gain access to "Начать дежурство" (Start duty).

Revoke the role using "Удалить из дежурных по опозданиям" (Remove from morning duty) in every bot where it was assigned. This does not interrupt an already active duty session. Granting administrator permissions is covered in the [technical guide](admin_management.md).

## Morning Duty

1. Select "Начать дежурство" (Start duty), then choose a building.
2. Enter the late student's surname; provide their given name if needed.
3. Select the student after checking their full name and class, then enter the reason for the late arrival.
4. Wait for "Опоздание записано" (Late arrival recorded), then enter the next student.
5. Select "Завершить дежурство" (Finish duty) **on the same day**. Closing the chat does not finish the duty session.

"Отмена" (Cancel) cancels the current input. The late-arrival time is recorded when the reason is saved; saved records cannot be edited through the bot.

## Export to Google Sheets

A late arrival is saved to the database first, then the bot attempts to send it to Sheets. Completed duty sessions and pending late arrivals are exported at these Moscow times:

| Bot | Times |
| --- | --- |
| TG | 10:30, 18:00, 00:30 |
| VK | 10:40, 18:10, 00:40 |

The bot must be running and have access to Sheets. Recording a new late arrival also retries the pending queue; unfinished duty sessions are not exported.

## Troubleshooting

- No "Начать дежурство" (Start duty): check registration and the assigned role in this specific bot.
- A student is missing: contact the person responsible for the "Ученики" worksheet. The list refreshes on the next search after the cache resets at **23:00**, or after the relevant bot is restarted.
- The bot is unresponsive: do not repeat an entry without checking it first, as this can create duplicates. The responsible person makes corrections in Sheets.
- You need to switch messengers: notify an administrator and record only subsequent late arrivals in the other messenger. Existing records and the start time are not transferred, and the first duty session does not finish automatically.
- After a restart, unsaved input must be entered again. Starting a duty again on the same day resumes a session that has not yet been exported, keeping its original start time and updating the building.

If you forgot to finish a duty session, or an entry is missing after the scheduled export, notify an administrator. For technical problems, use "Сообщить об ошибке" (Report an error) and include the time, messenger, and your most recent actions. Hide other people's personal information before sending a screenshot.
