import asyncio
from asyncio import sleep
from datetime import time

from freezegun import freeze_time
from pytest_mock import MockerFixture

from school_routine_bot.task_runner import TaskRunner


@freeze_time("2000-05-10 12:59:59.900000", tick=True)
async def test_task_runner_once_a_day(mocker: MockerFixture):
    task_before_start = mocker.AsyncMock()
    task_after_start = mocker.AsyncMock()

    scheduler = TaskRunner()

    scheduler.add_daily_task(task_before_start, time(13, 00))
    asyncio.create_task(scheduler.start())
    await sleep(0.01)
    scheduler.add_daily_task(task_after_start, time(13, 00))

    await sleep(0.2)
    assert task_before_start.call_count == 1
    assert task_after_start.call_count == 1


@freeze_time("2000-05-10 23:59:59.900000", tick=True)
async def test_task_runner_tomorrow(mocker: MockerFixture):
    scheduler = TaskRunner()
    asyncio.create_task(scheduler.start())

    task = mocker.AsyncMock()
    scheduler.add_daily_task(task, time(00, 00, 00, 200000))

    await sleep(0.5)
    assert task.call_count == 1
