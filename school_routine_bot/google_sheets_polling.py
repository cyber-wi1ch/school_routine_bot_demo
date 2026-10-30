import datetime
from asyncio import sleep
from copy import deepcopy
from pathlib import Path
from typing import Awaitable, Callable

import gspread
from google.auth.exceptions import TransportError
from gspread import Client, Worksheet
from gspread.exceptions import APIError
from loguru import logger
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout as RequestsTimeout

NETWORK_EXCEPTIONS = (
    ConnectionError,
    RequestsConnectionError,
    RequestsTimeout,
    TransportError,
)

actual_duty_data_for_both_worksheets: dict = {
    "Запись на дежурства": {},
}


def connect(
    credentials_file: Path | str, spreadsheet_url: str, page_title: str
) -> tuple[Client, Worksheet]:
    access: Client = gspread.service_account(credentials_file)
    worksheet: Worksheet = access.open_by_url(spreadsheet_url).worksheet(page_title)
    return access, worksheet


class NoSuitableDatesFoundError(ValueError):
    pass


class GoogleSheetsPolling:
    def __init__(
        self,
        page_title: str,
        credentials_file: Path | str,
        spreadsheet_url: str,
    ):
        self.page_title = page_title
        self.credentials_file = credentials_file
        self.spreadsheet_url = spreadsheet_url
        self.access, self.worksheet = connect(
            self.credentials_file, self.spreadsheet_url, self.page_title
        )

    def _reconnect(self):
        self.access, self.worksheet = connect(
            self.credentials_file, self.spreadsheet_url, self.page_title
        )

    @staticmethod
    def _get_start_date(date_col) -> str:
        for date in date_col:
            try:
                if (
                    datetime.datetime.strptime(date, "%d.%m.%Y").date()
                    >= datetime.date.today()
                ):
                    return date
            except ValueError:
                pass
        raise NoSuitableDatesFoundError(
            f"There are no suitable dates in the sheets data. {date_col=}"
        )

    def _get_start_and_stop_date_indexes(self, date_col, start_date) -> tuple[int, int]:
        all_dates = [str(s) for s in date_col if s]
        stop_date = ""
        other_col_for_getting_the_end_of_records = self.worksheet.col_values(6)
        len_for_stop_point = len(other_col_for_getting_the_end_of_records)
        for date_index, date in enumerate(all_dates):
            if date == start_date:
                try:
                    stop_date = all_dates[date_index + 3]
                except IndexError:
                    if len_for_stop_point != 0:
                        return date_col.index(start_date), len_for_stop_point
                    return 1, 1
        return date_col.index(start_date), date_col.index(stop_date)

    async def get_the_updated_worksheet(
        self, notify_new_records: Callable[[list[dict]], Awaitable]
    ):
        logger.success("Start polling")
        last_data = None
        while True:
            try:
                date_col = self.worksheet.col_values(1)
                await sleep(4)
                start_date = self._get_start_date(date_col)
                (
                    start_date_index,
                    stop_date_index,
                ) = self._get_start_and_stop_date_indexes(date_col, start_date)
                await sleep(4)
                cell_range = f"A{start_date_index + 1}:G{stop_date_index}"
                records = self.worksheet.get_all_values(cell_range)
                await sleep(4)
                if last_data != records:
                    last_data = records

                    logger.info(f"New data have come {len(records)=}")
                    await notify_new_records(deepcopy(records))
            except NoSuitableDatesFoundError as e:
                if last_data is not None:
                    last_data = None
                    logger.info(f"The table became empty: {e}")
                    await notify_new_records([])
            except APIError as e:
                if str(e.code).startswith("5"):
                    logger.info(
                        "Google Sheets returned an internal error",
                        f"(not our problem): {e}",
                    )
                else:
                    logger.error(f"We have got a Google API error: {e}")
            except NETWORK_EXCEPTIONS as e:
                logger.warning(
                    f"Google Sheets connection failed, trying to reconnect: {e}"
                )
                try:
                    self._reconnect()
                except NETWORK_EXCEPTIONS as reconnect_error:
                    logger.warning(
                        "Google Sheets reconnect failed, will retry on next polling "
                        f"iteration: {reconnect_error}"
                    )
            await sleep(6)
