from asyncio import sleep
from datetime import datetime

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture

from school_routine_bot.notify_at_once_school_scheduler_impl import (
    NotifyAtOnceSchoolSchedulerImpl,
)
from school_routine_bot.pydantic_schemes import InvalidDutyRow, ValidDutyRow
from school_routine_bot.school_scheduler import prepare_to_notify_admins


@freeze_time("2025-10-28 11:48:10.909", tick=True)
async def test_new_duties(mocker: MockerFixture):
    notify_at_once_logic = NotifyAtOnceSchoolSchedulerImpl(
        "test_admin_base.json", notify_mock := mocker.AsyncMock(), ""
    )

    valid_duty_data: dict[str, list[ValidDutyRow]] = {
        "известная-фамилия": [
            ValidDutyRow(
                date=datetime.strptime("28.10.2025", "%d.%m.%Y").date(),
                location="4 этаж 1 корпус",
                time_1=datetime.strptime("12:40", "%H:%M").time(),
                time_2=datetime.strptime("12:50", "%H:%M").time(),
                duration=10,
                chat_id=123,
                name="илья",
                by_father_name="отчество",
                exact_name_from_table="известная-фамилия",
            )
        ]
    }

    await notify_at_once_logic.set_table_data({}, {}, {})
    await notify_at_once_logic.set_table_data(valid_duty_data, {}, {})

    await sleep(0.1)

    assert notify_mock.call_count == 0


@pytest.mark.xfail
@freeze_time("2025-10-28 11:48:10.909", tick=True)
async def test_new_duties_with_no_registered_user(
    mocker: MockerFixture, caught_logs: list[str]
):
    notify_at_once_logic = NotifyAtOnceSchoolSchedulerImpl(
        "test_admin_base.json", notify_mock := mocker.AsyncMock(), ""
    )

    invalid_duty_data = {
        "неизвестная-фамилия": [
            InvalidDutyRow(
                date="28.10.2025",
                time="12:40 - 12:50",
                location="4 этаж 1 корпус",
                duration="10",
                chat_id=None,
                exact_name_from_table="неизвестная-фамилия",
                name=None,
                by_father_name=None,
            )
        ]
    }

    await notify_at_once_logic.set_table_data({}, {}, {})
    await notify_at_once_logic.set_table_data({}, {}, invalid_duty_data)

    await sleep(0.1)
    admins = prepare_to_notify_admins(notify_at_once_logic.admin_base)
    assert notify_mock.call_count == len(admins)
    for sent_id, sent_message in [el[0] for el in notify_mock.call_args_list]:
        assert str(sent_id) in admins
        assert "этот человек еще не зарегистрирован в боте" in sent_message
    assert (
        "cannot write to unknown user: неизвестная-фамилия"
        in " ".join(caught_logs).lower()
    )
