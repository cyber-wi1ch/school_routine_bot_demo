from datetime import datetime, time
from typing import Callable

from loguru import logger

from school_routine_bot.notify_at_once_school_scheduler_impl import (
    notify_people_about_what_have_changed,
)
from school_routine_bot.pydantic_schemes import (
    AvailableDutySlots,
    InvalidDutyRow,
    ValidDutyRow,
)
from school_routine_bot.school_scheduler import (
    SchoolScheduler,
    assemble_duty_info_for_each_person,
    get_available_ids_and_not_bot_users,
    get_next_datetime,
    is_it_not_saturday,
    prepare_to_notify_admins,
    sort_data_by_certain_time_for_av_duty_slots_and_invalid_data,
    sort_data_by_certain_time_period,
    turn_empty_duty_slots_into_message,
    turn_names_into_column,
)
from school_routine_bot.task_runner import TaskRunner

scheduler = TaskRunner()


class NotifyAllSchoolSchedulerImpl(SchoolScheduler):
    def __init__(
        self,
        admin_base: str,
        notify: Callable,
        page_title: str,
        notification_time: time = time(13, 0),
        renotification_time: time = time(17, 0),
        _scheduler: TaskRunner = scheduler,
    ):
        super().__init__(notify)
        logger.info(f"Notification time: {notification_time}")
        _scheduler.add_daily_task(self._notify_all, notification_time)
        _scheduler.add_daily_task(
            self._notify_people_about_what_have_changed_from_13_to_17,
            renotification_time,
        )
        self.admin_base = admin_base
        self.data: dict = {}
        self.data_from_last_notify_all: dict | None = None
        self.page_title = page_title
        self.available_duties: dict[str, list[AvailableDutySlots]] = {}
        self.invalid_duties: dict[str, list[InvalidDutyRow]] = {}

    async def _notify_admins(self, message: str):
        logger.info(f"Notify admins called: {self.admin_base=}")
        for admin_id, admin_name in prepare_to_notify_admins(self.admin_base).items():
            await self.notify(
                admin_id,
                f"{admin_name}, {message}",
                parse_mode="html",
            )

    async def set_table_data(
        self,
        valid_data: dict[str, list[ValidDutyRow]],
        available_data: dict[str, list[AvailableDutySlots]],
        invalid_data: dict[str, list[InvalidDutyRow]],
    ):
        self.data, self.available_duties, self.invalid_duties = (
            valid_data,
            available_data,
            invalid_data,
        )
        if self.data_from_last_notify_all is None:
            self.data_from_last_notify_all = self.data

    async def _notify_all(self):
        try:
            self.data_from_last_notify_all = self.data

            (
                sorted_empty_slots,
                sorted_invalid_duties,
            ) = sort_data_by_certain_time_for_av_duty_slots_and_invalid_data(
                self.available_duties, self.invalid_duties
            )

            sorted_data = sort_data_by_certain_time_period(self.data)
            logger.debug(f"Notify all called: {sorted_data=}")

            people_ids, not_users = get_available_ids_and_not_bot_users(
                sorted_data, sorted_invalid_duties
            )
            for person_id in people_ids:
                for message in assemble_duty_info_for_each_person(
                    person_id, sorted_data
                ):
                    if is_it_not_saturday():
                        await self.notify(person_id, message, parse_mode="html")

            if empty_slots := sorted_empty_slots.get(""):
                await self._notify_admins(
                    "нет дежурных на следующие дежурства:"
                    f"\n\n {turn_empty_duty_slots_into_message(empty_slots)}"
                )

            if not_users:
                await self._notify_admins(
                    f"эти дежурные "
                    "не зарегистрированы в Telegram-боте"
                    " - не могу предупредить "
                    "их о дежурствах в Telegram:"
                    "\n"
                    f"\n{turn_names_into_column(not_users)}"
                    "(Но эти люди могут быть зарегистрированы и предупреждены в ВК-версии. Требует уточнения.)"
                )
        except Exception as e:
            logger.error(e)
            raise

    async def _notify_people_about_what_have_changed_from_13_to_17(self):
        await notify_people_about_what_have_changed(
            self.admin_base,
            old_data=self.data_from_last_notify_all,
            page_title=self.page_title,
            invalid_data=self.invalid_duties,
            new_data=self.data,
            from_time=datetime.now(),
            to_time=get_next_datetime(at=time(17, 0)),
            notify=self.notify,
            notify_about_added=True,
        )
