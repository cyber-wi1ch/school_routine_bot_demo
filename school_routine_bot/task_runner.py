import asyncio
from datetime import date, datetime, time
from typing import Awaitable, Callable

from loguru import logger

from school_routine_bot.school_scheduler import get_next_datetime


class TaskRunner:
    def __init__(self):
        self.tasks = []
        self.started = False

    @staticmethod
    def _get_sec_until_next(target_time: time) -> float:
        next_run = get_next_datetime(target_time)
        return (next_run - datetime.now()).total_seconds()

    @staticmethod
    def _it_will_shoot_today(target_time) -> bool:
        return get_next_datetime(target_time).date() == date.today()

    def add_daily_task(self, func: Callable[[], Awaitable[None]], target_time: time):
        self.tasks.append((target_time, func))
        if self.started:
            self._reschedule_for_today(target_time, func)

    def _reschedule_for_today(
        self, target_time: time, func: Callable[[], Awaitable[None]]
    ):
        if self._it_will_shoot_today(target_time):
            next_run = get_next_datetime(target_time)
            logger.trace(f"Task {func} is planned to run at {next_run}")
            asyncio.create_task(
                self._run_task(func, (next_run - datetime.now()).total_seconds())
            )
        else:
            logger.trace(f"Task {func} cannot be planned for today at {target_time}")

    async def _run_task(self, func, delay: float):
        await asyncio.sleep(delay)
        logger.trace(f"Task {func} is about to run")
        # noinspection PyBroadException
        try:
            await func()
        except Exception as e:
            logger.exception(f"Some task in task_runner failed to run: {e}")

    async def start(self):
        if not self.started:
            self.started = True
            while True:
                logger.trace("Rescheduling loop started")
                for target_time, func in self.tasks:
                    self._reschedule_for_today(target_time, func)
                next_run = get_next_datetime(time(0, 0))
                logger.trace(f"Next rescheduling loop is planned for {next_run}")
                await asyncio.sleep((next_run - datetime.now()).total_seconds())
