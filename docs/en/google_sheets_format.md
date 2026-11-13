# Google Sheets Format

[Русский](../google_sheets_format.md) | English

[README](../../README.en.md)

The service works with two Google spreadsheets and requires two URLs: `table_url` for the duty schedule covering floors and locations, and `morning_duty_table_url` for morning entrance duties and late arrivals. The spreadsheets must contain all worksheets referenced by the bot's code. Worksheet names and column order must match the specification below.

Keep the Russian worksheet names and sample headers unchanged: they describe the bot's existing data format, not a translated interface.

## Duty Sign-Up: "Запись на дежурства"

Headers occupy A1:G1; data starts in row 2. Paste this tab-separated block into A1. Replace the example dates with current dates.

```text
Дата	Ответственный	Место	Время	Выбранное время	Минуты	Дежурный
28.09.2026	Александрова Александра Александровна	Первый этаж	08:00 - 08:30		30	Иванов Иван Иванович
	Александрова Александра Александровна	Второй этаж	08:30 - 09:00		30	Иванов Иван Иванович
29.09.2026	Александрова Александра Александровна	Первый этаж	08:00 - 08:30		30	Иванов Иван Иванович
```

- **A:** date in `DD.MM.YYYY` format, entered once at the start of a block. Blocks must be in ascending date order; leave A empty in the remaining rows of each block.
- **B-D:** coordinator, location, and time interval. Fill in the first row of the block; empty A-D cells below inherit the preceding values.
- **E:** optional time interval overriding D, for example `08:10 - 08:30`.
- **F:** duration in minutes. The bot recalculates the duration, but this column must still be filled in: it is used to detect the end of the data when there are not enough subsequent dates.
- **G:** the person's full name exactly as registered with the bot; an empty cell means an unfilled slot.

Use intervals within a single day. Format column A as `DD.MM.YYYY` or plain text. Do not insert service rows between duties. The bot reads up to three upcoming blocks, starting with today's or the next available date.

Column B does not grant administrator permissions or configure notification recipients. Currently, only the "Запись на дежурства" worksheet is read from the duty schedule.

## Students: "Ученики"

Paste the headers into A1 and add students below. Put the surname first; grade and class letter must be in separate columns.

```text
ФИО	Класс	Буква
Сидоров Сидор Сидорович	7	А
Тестова Тестина Тестовна	8	Б
```

The first row is skipped. Each running bot clears its student-list cache daily at **23:00 Moscow time**. The updated list is loaded from the spreadsheet on the next student search. To apply changes immediately, ask technical staff to restart the relevant bot.

## Late Arrivals and Morning Duties

Create worksheets named "Опоздавшие" and "Утренние дежурства". Paste the corresponding headers into A1; the bot fills in the rows below.

**"Опоздавшие" (Late arrivals), A:H:**

```text
ФИО дежурного	ФИО ученика	Класс	Буква	Дата	Время	Корпус	Причина
```

**"Утренние дежурства" (Morning duties), A:E:**

```text
Дата	Корпус	Начало	Завершение	ФИО дежурного
```

Dates use `DD.MM.YYYY`; times use `HH:MM`. The demo building labels are "Корпус А" and "Корпус Б" (Building A and Building B).
