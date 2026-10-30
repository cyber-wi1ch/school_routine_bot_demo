import asyncio
import sys
from asyncio import sleep
from datetime import datetime, time

from freezegun import freeze_time
from loguru import logger
from pytest_mock import MockerFixture

from school_routine_bot.notify_all_school_scheduler_impl import (
    NotifyAllSchoolSchedulerImpl,
)
from school_routine_bot.pydantic_schemes import ValidDutyRow
from school_routine_bot.task_runner import TaskRunner


@freeze_time("2025-10-09 12:59:59.900000", tick=True)
async def test_notify_all(mocker: MockerFixture):
    notify_mock = mocker.AsyncMock()
    scheduler = TaskRunner()
    asyncio.create_task(scheduler.start())

    notify_all_scheduler = NotifyAllSchoolSchedulerImpl(
        "test_admin_base.json", notify_mock, _scheduler=scheduler, page_title=""
    )
    valid_duty_data: dict[str, list[ValidDutyRow]] = {
        "иванов": [
            ValidDutyRow(
                date=datetime.strptime("09.10.2025", "%d.%m.%Y").date(),
                location="холодильник",
                time_1=datetime.strptime("18:10", "%H:%M").time(),
                time_2=datetime.strptime("18:30", "%H:%M").time(),
                duration=20,
                chat_id=123,
                name="иван",
                by_father_name="иванович",
                exact_name_from_table="иванов сергей михайлович",
            )
        ]
    }

    await notify_all_scheduler.set_table_data(
        valid_duty_data,
        {},
        {},
    )

    await sleep(0.4)

    assert notify_mock.call_count == 1
    sent_id, sent_message = notify_mock.call_args[0]
    assert sent_id == 123
    assert "Иван Иванович" in sent_message
    assert "18:10 - 18:30" in sent_message
    assert "холодильник" in sent_message


@freeze_time("2025-10-09 23:59:59.900000", tick=True)
async def test_notify_all_tomorrow(mocker: MockerFixture):
    notify_mock = mocker.AsyncMock()
    scheduler = TaskRunner()
    asyncio.create_task(scheduler.start())

    notify_all_scheduler = NotifyAllSchoolSchedulerImpl(
        "test_admin_base.json",
        notify_mock,
        "",
        time(0, 0, 0, 200000),
        _scheduler=scheduler,
    )

    valid_duty_data: dict[str, list[ValidDutyRow]] = {
        "иванов": [
            ValidDutyRow(
                date=datetime.strptime("10.10.2025", "%d.%m.%Y").date(),
                location="холодильник",
                time_1=datetime.strptime("18:10", "%H:%M").time(),
                time_2=datetime.strptime("18:30", "%H:%M").time(),
                duration=20,
                chat_id=123,
                name="иван",
                by_father_name="иванович",
                exact_name_from_table="иванов сергей михайлович",
            )
        ]
    }

    await notify_all_scheduler.set_table_data(
        valid_duty_data,
        {},
        {},
    )

    await sleep(0.4)

    assert notify_mock.call_count == 1
    sent_id, sent_message = notify_mock.call_args[0]
    assert sent_id == 123
    assert "Иван Иванович" in sent_message
    assert "18:10 - 18:30" in sent_message
    assert "холодильник" in sent_message


logger.add(sys.stdout, level="TRACE")


@freeze_time("2025-10-09 16:59:57", tick=True)
async def test_13_17(mocker: MockerFixture):
    notify_mock = mocker.AsyncMock()
    scheduler = TaskRunner()
    asyncio.create_task(scheduler.start())

    notify_all_scheduler = NotifyAllSchoolSchedulerImpl(
        "test_admin_base.json",
        notify_mock,
        "",
        _scheduler=scheduler,
        notification_time=time(16, 59, 59, 500000),
        renotification_time=time(17, 00),
    )

    valid_duty_data: dict[str, list[ValidDutyRow]] = {
        "иванов": [
            ValidDutyRow(
                date=datetime.strptime("10.10.2025", "%d.%m.%Y").date(),
                location="холодильник",
                time_1=datetime.strptime("16:10", "%H:%M").time(),
                time_2=datetime.strptime("16:30", "%H:%M").time(),
                duration=20,
                chat_id=123,
                name="иван",
                by_father_name="иванович",
                exact_name_from_table="иванов сергей михайлович",
            )
        ]
    }

    valid_duty_data_1: dict[str, list[ValidDutyRow]] = {
        "иванов": [
            ValidDutyRow(
                date=datetime.strptime("10.10.2025", "%d.%m.%Y").date(),
                location="кухня",
                time_1=datetime.strptime("16:10", "%H:%M").time(),
                time_2=datetime.strptime("16:30", "%H:%M").time(),
                duration=20,
                chat_id=123,
                name="иван",
                by_father_name="иванович",
                exact_name_from_table="иванов сергей михайлович",
            )
        ]
    }

    await notify_all_scheduler.set_table_data(
        valid_duty_data,
        {},
        {},
    )

    await notify_all_scheduler.set_table_data(
        valid_duty_data,
        {},
        {},
    )

    await sleep(2.6)

    assert notify_mock.call_count == 1
    sent_id, sent_message = notify_mock.call_args_list[0][0]
    assert sent_id == 123
    assert "Иван Иванович" in sent_message
    assert "16:10 - 16:30" in sent_message
    assert "холодильник" in sent_message

    await notify_all_scheduler.set_table_data(valid_duty_data_1, {}, {})

    await sleep(1)
    assert notify_mock.call_count == 2
    sent_id, sent_message = notify_mock.call_args_list[1][0]
    assert sent_id == 123
    assert "кухня" in sent_message
