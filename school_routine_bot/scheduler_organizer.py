import asyncio
from typing import Callable

from loguru import logger

from school_routine_bot.convert_data_to_pydantic_schemes import (
    convert_data_to_pydantic_schemes,
)
from school_routine_bot.google_sheets_polling import (
    actual_duty_data_for_both_worksheets,
)
from school_routine_bot.matcher_school_bot_users import MatcherSchoolBotUsers
from school_routine_bot.notify_all_school_scheduler_impl import (
    NotifyAllSchoolSchedulerImpl,
)
from school_routine_bot.notify_at_once_school_scheduler_impl import (
    NotifyAtOnceSchoolSchedulerImpl,
)
from school_routine_bot.notify_in_advance_school_scheduler_impl import (
    NotifyInAdvanceSchoolSchedulerImpl,
)
from school_routine_bot.school_scheduler import (
    SchoolScheduler,
    make_the_duty_data_info_actual,
    turn_english_alike_letters_into_russian,
)


def cut_out_the_surname(name_from_table: str):
    name_from_table = turn_english_alike_letters_into_russian(name_from_table.strip())
    index = name_from_table.find(" ")
    if index == -1:
        return name_from_table.lower()
    return name_from_table[:index].lower()


def convert_duty_data_to_dict(duty_data: list[list]) -> dict:
    duty_storage: dict = {}
    for row in duty_data:
        if len(row) == 7:
            date, admin, location, time, user_choice_time, duration, person = row
        elif len(row) == 6:
            date, admin, location, time, user_choice_time, duration = row
            person = ""
        else:
            continue
        duty_data_row = {
            "date": date.strip().lower(),
            "admin": admin.strip().lower(),
            "location": location.strip().lower(),
            "time": time.strip().lower(),
            "user_choice_time": user_choice_time.strip().lower(),
            "duration": duration.strip().lower(),
            "exact_name_from_table": turn_english_alike_letters_into_russian(
                person.lower()
            ),
        }
        duty_storage[cut_out_the_surname(person)] = duty_storage.get(
            cut_out_the_surname(person), []
        ) + [duty_data_row]
    return duty_storage


def fill_in_gaps_except_for_some_last_cols(actual_data: list) -> list:
    if actual_data:
        rows = len(actual_data)
        cols = len(actual_data[0])
        for r in range(rows):
            for c in range(cols):
                excluded_cols = 4, 5, 6
                if actual_data[r][c] == "" and c not in excluded_cols:
                    actual_data[r][c] = actual_data[r - 1][c]
                    continue
        return actual_data
    return []


def apply_choice_time(duty_data: dict) -> dict:
    for person, duties in duty_data.items():
        for duty in duties:
            if user_choice_time := duty.pop("user_choice_time", None):
                duty["time"] = user_choice_time
    return duty_data


class SchedulerOrganizer:
    def __init__(
        self,
        page_title: str,
        matcher: MatcherSchoolBotUsers,
        admin_base: str,
        notify: Callable,
    ):
        self.page_title = page_title
        self.routines: list[SchoolScheduler] = [
            NotifyAllSchoolSchedulerImpl(admin_base, notify, self.page_title),
            NotifyAtOnceSchoolSchedulerImpl(admin_base, notify, self.page_title),
            NotifyInAdvanceSchoolSchedulerImpl(notify),
        ]
        self._matcher = matcher
        self.notify = notify

    async def set_table_data(self, valid_data, available_data, invalid_data):
        await asyncio.gather(
            *[
                routine.set_table_data(valid_data, available_data, invalid_data)
                for routine in self.routines
            ]
        )

    async def handle_new_data(self, records):
        dict_data = apply_choice_time(
            convert_duty_data_to_dict(fill_in_gaps_except_for_some_last_cols(records))
        )
        matched_duties = self._matcher.add_id_if_match(dict_data)
        valid_data, available_data, invalid_data = convert_data_to_pydantic_schemes(
            make_the_duty_data_info_actual(matched_duties)
        )

        actual_duty_data_for_both_worksheets[self.page_title] = valid_data

        await self.set_table_data(valid_data, available_data, invalid_data)

        logger.info(f"New data has been handled: {len(records)=}")
