from datetime import date

import pytest

from school_routine_bot.google_sheets_polling import GoogleSheetsPolling


@pytest.mark.parametrize(
    "date_list, the_date",
    [
        (
            [
                "",
                "",
                "Date",
                "Дата",
                "13.09.2025",
                "",
                f"24.09.{date.today().year + 1}",
            ],
            f"24.09.{date.today().year + 1}",
        ),
        (
            [
                "13.08.25",
                "Date",
                f"27.09.{date.today().year + 1}",
                "",
                f"29.09.{date.today().year + 1}",
            ],
            f"27.09.{date.today().year + 1}",
        ),
        (
            ["Дата", "25.01.24", "", "", "", f"01.01.{date.today().year + 1}"],
            f"01.01.{date.today().year + 1}",
        ),
    ],
)
def test_get_start_date(date_list: list[str], the_date: str):
    google_sheets_polling = GoogleSheetsPolling.__new__(GoogleSheetsPolling)
    assert google_sheets_polling._get_start_date(date_list) == the_date


def test_get_start_date_without_valid_data():
    with pytest.raises(ValueError) as no_suitable_dates_error:
        google_sheets_polling = GoogleSheetsPolling.__new__(GoogleSheetsPolling)
        google_sheets_polling._get_start_date(["Date", "19.09.24", "", "", "19.09.25"])
    assert "There are no suitable dates in the sheets data." in str(
        no_suitable_dates_error
    )
