import asyncio
from asyncio import Task
from datetime import datetime, time
from typing import Callable

from loguru import logger

from school_routine_bot.manage_sent_reminders import ManageSentReminders
from school_routine_bot.pydantic_schemes import ValidDutyRow
from school_routine_bot.school_scheduler import (
    SchoolScheduler,
    cut_time_points_out_of_str,
)

path_to_sent_reminders = "../sent_reminders.json"
manage_sent_reminders_instance: ManageSentReminders = ManageSentReminders(
    path_to_sent_reminders
)


def is_it_work_time_for_today() -> bool:
    start = datetime.now().replace(hour=8, minute=0)
    end = datetime.now().replace(hour=18, minute=0)
    now = datetime.now().now()
    logger.info(f"\nSTART AT {start}\nNOW AT {now}\nEND AT {end}")
    if start <= now <= end:
        return True
    manage_sent_reminders_instance.clean_sent_reminders()
    return False


def prepare_to_notify_in_advance(duty: ValidDutyRow) -> bool:
    time_point_1, time_point_2 = cut_time_points_out_of_str(duty.time_period_str)
    duty_date = duty.date
    if time_point_1:
        if duty_date == datetime.today().date():
            hours, mins = time_point_1.split(":")
            duty_time = time(int(hours), int(mins))
            dt_duty_time = datetime.combine(datetime.today(), duty_time)
            diff = dt_duty_time - datetime.today()
            dt_hours = diff.total_seconds() // 3600
            dt_mins = (diff.total_seconds() % 3600) // 60
            if dt_hours == 0:
                if 0 < dt_mins <= 14:
                    logger.info(f"DIFF MINUTES {dt_mins=}")
                    return True
            return False
        return False
    return False


def check_if_notification_was_sent(duty_for_check: ValidDutyRow, chat_id: int) -> bool:
    duty_for_check_dict: dict = duty_for_check.model_dump(mode="json")
    sent_notifications = manage_sent_reminders_instance.get_sent_reminders()
    if chat_id in sent_notifications:
        date, duty_time, location, exact_name = (
            duty_for_check_dict.get("date_str", ""),
            duty_for_check_dict.get("time_period_str", ""),
            duty_for_check_dict.get("location", ""),
            duty_for_check_dict.get("exact_name_from_table", ""),
        )
        for duty in sent_notifications[chat_id]:
            if date.strip() != duty.get("date_str").strip():
                continue
            if duty_time.strip() != duty.get("time_period_str").strip():
                continue
            if location.strip() != duty.get("location").strip():
                continue
            if exact_name.strip() != duty.get("exact_name_from_table").strip():
                continue
            else:
                return True
        return False
    else:
        return False


async def notify_15_minutes_before(actual_data: dict[str, list[ValidDutyRow]], notify):
    logger.info(f"Notify in advance was called: {len(actual_data)=}")
    logger.info(f"SENT -> {manage_sent_reminders_instance.sent_reminders=}")
    if actual_data:
        for person, duties in actual_data.items():
            for duty in duties:
                if duty.chat_id:
                    if prepare_to_notify_in_advance(
                        duty
                    ) and not check_if_notification_was_sent(duty, duty.chat_id):
                        sent = await notify(
                            duty.chat_id,
                            f"<b>Внимание❗</b>\n"
                            f"🔔Скоро начнётся "
                            f"Ваше дежурство:\n "
                            f"<b>место</b> - "
                            f"<u>{duty.location}</u>,"
                            f"\n <b>время</b> -"
                            f" <u>{duty.time_period_str}.</u>\n "
                            f"Не пропустите его! 🤍",
                            parse_mode="html",
                        )

                        if not sent:
                            continue

                        manage_sent_reminders_instance.add_duty_to_sent_reminders(
                            duty.chat_id, duty
                        )
                        logger.warning(
                            f" WAS NOTIFIED: {duty.exact_name_from_table.upper()}"
                        )
                        logger.info(
                            f"SENT_INFO -> {manage_sent_reminders_instance.sent_reminders=}"
                        )
                        continue
                    else:
                        continue
                else:
                    continue

    else:
        logger.info(f"Empty data came {actual_data=}")


class NotifyInAdvanceSchoolSchedulerImpl(SchoolScheduler):
    def __init__(self, notify: Callable):
        super().__init__(notify)
        self.data: dict[str, list[ValidDutyRow]] | None = None
        self.searching_task: Task | None = None

    async def _start_searching_duties_to_notify_about(self):
        while True:
            try:
                if is_it_work_time_for_today():
                    await notify_15_minutes_before(self.data, notify=self.notify)
                    await asyncio.sleep(60)
                else:
                    await asyncio.sleep(3600)
            except Exception as e:
                logger.exception(e)
                await asyncio.sleep(5)

    async def set_table_data(self, valid_data, available_data, invalid_data):
        new_data = {key: value for key, value in valid_data.items() if key}
        valid_duties = new_data
        if self.data is None:
            self.data = valid_duties
            self.searching_task = asyncio.create_task(
                self._start_searching_duties_to_notify_about()
            )
        self.data = valid_duties
