from datetime import datetime

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture

from school_routine_bot import notify_in_advance_school_scheduler_impl as reminders
from school_routine_bot.notify_in_advance_school_scheduler_impl import (
    check_if_notification_was_sent,
    is_it_work_time_for_today,
    manage_sent_reminders_instance,
    notify_15_minutes_before,
    prepare_to_notify_in_advance,
)
from school_routine_bot.pydantic_schemes import ValidDutyRow


@pytest.fixture(autouse=True)
def user_test_sent_reminders_json(mocker):
    mocker.patch.object(
        manage_sent_reminders_instance,
        "sent_reminders_path",
        new="test_sent_reminders.json",
    )


@pytest.mark.parametrize(
    "now, bool_answer",
    [
        ("23:59:59.900000", False),
        ("07:59:59.900000", False),
        ("03:59:59.900000", False),
        ("13:59:59.900000", True),
        ("17:59:59.900000", True),
        ("08:59:59.900000", True),
    ],
)
def test_is_it_work_time_for_today(now, bool_answer):
    with freeze_time(now):
        assert is_it_work_time_for_today() is bool_answer


@pytest.mark.parametrize(
    "now, duty, bool_answer",
    [
        (
            "2025-10-09 13:09:59.900000",
            ValidDutyRow(
                date=datetime.strptime("19.10.2025", "%d.%m.%Y").date(),
                time_1=datetime.strptime("10:40", "%H:%M").time(),
                time_2=datetime.strptime("10:50", "%H:%M").time(),
                location="2 этаж 2 корпус",
                duration=10,
                chat_id=34567890,
                exact_name_from_table="тестова",
            ),
            False,
        ),
        (
            "2025-10-09 07:59:59.900000",
            ValidDutyRow(
                date=datetime.strptime("09.10.2025", "%d.%m.%Y").date(),
                time_1=datetime.strptime("10:40", "%H:%M").time(),
                time_2=datetime.strptime("10:50", "%H:%M").time(),
                location="2 этаж 2 корпус",
                duration=10,
                chat_id=34567890,
                exact_name_from_table="тестова",
            ),
            False,
        ),
        (
            "2025-10-09 13:59:59.900000",
            ValidDutyRow(
                date=datetime.strptime("09.10.2025", "%d.%m.%Y").date(),
                time_1=datetime.strptime("10:40", "%H:%M").time(),
                time_2=datetime.strptime("10:50", "%H:%M").time(),
                location="2 этаж 2 корпус",
                duration=10,
                chat_id=34567890,
                exact_name_from_table="тестова",
            ),
            False,
        ),
        (
            "2025-10-09 10:25:59.900000",
            ValidDutyRow(
                date=datetime.strptime("09.10.2025", "%d.%m.%Y").date(),
                time_1=datetime.strptime("10:40", "%H:%M").time(),
                time_2=datetime.strptime("10:50", "%H:%M").time(),
                location="2 этаж 2 корпус",
                duration=10,
                chat_id=34567890,
                exact_name_from_table="тестова",
            ),
            True,
        ),
        (
            "2025-10-09 10:35:59.900000",
            ValidDutyRow(
                date=datetime.strptime("09.10.2025", "%d.%m.%Y").date(),
                time_1=datetime.strptime("10:40", "%H:%M").time(),
                time_2=datetime.strptime("10:50", "%H:%M").time(),
                location="2 этаж 2 корпус",
                duration=10,
                chat_id=34567890,
                exact_name_from_table="тестова",
            ),
            True,
        ),
        (
            "2025-10-09 10:38:59.900000",
            ValidDutyRow(
                date=datetime.strptime("09.10.2025", "%d.%m.%Y").date(),
                time_1=datetime.strptime("10:40", "%H:%M").time(),
                time_2=datetime.strptime("10:50", "%H:%M").time(),
                location="2 этаж 2 корпус",
                duration=10,
                chat_id=34567890,
                exact_name_from_table="тестова",
            ),
            True,
        ),
    ],
)
def test_prepare_to_notify_in_advance(now, duty: ValidDutyRow, bool_answer):
    with freeze_time(now):
        assert prepare_to_notify_in_advance(duty) is bool_answer


@pytest.mark.parametrize(
    "duty_for_check, chat_id, sent_notifications_for_test, bool_check_result",
    [
        (
            ValidDutyRow(
                date=datetime.strptime("19.09.2025", "%d.%m.%Y").date(),
                time_1=datetime.strptime("10:40", "%H:%M").time(),
                time_2=datetime.strptime("10:50", "%H:%M").time(),
                location="2 этаж 2 корпус",
                duration=10,
                chat_id=34567890,
                exact_name_from_table="тестова",
            ),
            "34567890",
            {
                "34567890": [
                    {
                        "date_str": "19.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time_period_str": "10:40 - 10:50",
                        "duration": "10",
                        "chat_id": "34567890",
                        "exact_name_from_table": "тестова",
                    },
                    {
                        "date_str": "20.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time_period_str": "10:40 - 10:50",
                        "duration": "10",
                        "chat_id": "34567890",
                        "exact_name_from_table": "тестова",
                    },
                ],
                "12309876": [
                    {
                        "date_str": "19.09.2025",
                        "admin": "Дежурный тьютор",
                        "location": "Столовая",
                        "time_period_str": "12:20 - 13:00",
                        "duration": "40",
                        "chat_id": "12309876",
                        "exact_name_from_table": "демов",
                    }
                ],
            },
            True,
        ),
        (
            ValidDutyRow(
                date=datetime.strptime("19.09.2025", "%d.%m.%Y").date(),
                time_1=datetime.strptime("10:40", "%H:%M").time(),
                time_2=datetime.strptime("10:50", "%H:%M").time(),
                location="2 этаж 2 корпус",
                duration=10,
                chat_id=34567891,
                exact_name_from_table="тестова а. и.",
            ),
            "34567891",
            {
                "34567890": [
                    {
                        "date_str": "19.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time_period_str": "10:40 - 10:50",
                        "duration": "10",
                        "chat_id": "34567890",
                        "exact_name_from_table": "тестова",
                    },
                    {
                        "date_str": "20.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time_period_str": "10:40 - 10:50",
                        "duration": "10",
                        "chat_id": "34567890",
                        "exact_name_from_table": "тестова",
                    },
                ],
                "12309876": [
                    {
                        "date_str": "19.09.2025",
                        "admin": "Дежурный тьютор",
                        "location": "Столовая",
                        "time_period_str": "12:20 - 13:00",
                        "duration": "40",
                        "chat_id": "12309876",
                        "exact_name_from_table": "демов",
                    }
                ],
            },
            False,
        ),
        (
            ValidDutyRow(
                date=datetime.strptime("19.09.2025", "%d.%m.%Y").date(),
                time_1=datetime.strptime("10:55", "%H:%M").time(),
                time_2=datetime.strptime("11:50", "%H:%M").time(),
                location="1 этаж 2 корпус",
                duration=10,
                chat_id=12309876,
                exact_name_from_table="демов",
            ),
            "12309876",
            {
                "34567890": [
                    {
                        "date_str": "19.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time_period_str": "10:40 - 10:50",
                        "duration": "10",
                        "chat_id": "34567890",
                        "exact_name_from_table": "тестова",
                    },
                    {
                        "date_str": "20.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time_period_str": "10:40 - 10:50",
                        "duration": "10",
                        "chat_id": "34567890",
                        "exact_name_from_table": "тестова",
                    },
                ],
                "12309876": [
                    {
                        "date_str": "19.09.2025",
                        "admin": "Дежурный тьютор",
                        "location": "Столовая",
                        "time_period_str": "12:20 - 13:00",
                        "duration": "40",
                        "chat_id": "12309876",
                        "exact_name_from_table": "демов",
                    }
                ],
            },
            False,
        ),
        (
            ValidDutyRow(
                date=datetime.strptime("19.09.2025", "%d.%m.%Y").date(),
                time_1=datetime.strptime("10:55", "%H:%M").time(),
                time_2=datetime.strptime("11:50", "%H:%M").time(),
                location="1 этаж 2 корпус",
                duration=10,
                chat_id=12309876,
                exact_name_from_table="демов",
            ),
            "12309876",
            {},
            False,
        ),
    ],
)
def test_check_if_notification_was_sent(
    mocker: MockerFixture,
    duty_for_check,
    chat_id,
    sent_notifications_for_test,
    bool_check_result,
):
    mocker.patch.object(
        manage_sent_reminders_instance,
        "get_sent_reminders",
        return_value=sent_notifications_for_test,
    )

    assert (
        check_if_notification_was_sent(duty_for_check, chat_id)
    ) is bool_check_result


@pytest.mark.parametrize(
    "now, actual_data, sent_reminders_for_test, count_number",
    [
        (
            "2025-10-09 09:59:59.900000",
            {},
            {
                34567890: [
                    {
                        "date_str": "09.10.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time_period_str": "10:40 - 10:50",
                        "duration": "10",
                        "chat_id": "34567890",
                        "exact_name_from_table": "тестова",
                    },
                    {
                        "date_str": "09.10.2025",
                        "admin": "Тестов",
                        "location": "3 этаж 2 корпус",
                        "time_period_str": "10:45 - 10:50",
                        "duration": "10",
                        "chat_id": "34567890",
                        "exact_name_from_table": "тестова",
                    },
                ],
                12309876: [
                    {
                        "date_str": "09.10.2025",
                        "admin": "Дежурный тьютор",
                        "location": "Столовая",
                        "time_period_str": "12:20 - 13:00",
                        "duration": "40",
                        "chat_id": "12309876",
                        "exact_name_from_table": "демов",
                    }
                ],
            },
            0,
        ),
        (
            "2025-10-09 10:00:59.900000",
            {
                "тестова": [
                    ValidDutyRow(
                        date=datetime.strptime("09.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:10", "%H:%M").time(),
                        time_2=datetime.strptime("10:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=10,
                        chat_id=34567890,
                        exact_name_from_table="тестова",
                    ),
                    ValidDutyRow(
                        date=datetime.strptime("09.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:50", "%H:%M").time(),
                        time_2=datetime.strptime("11:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=60,
                        chat_id=34567890,
                        exact_name_from_table="тестова",
                    ),
                ],
                "демов": [
                    ValidDutyRow(
                        date=datetime.strptime("09.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("12:20", "%H:%M").time(),
                        time_2=datetime.strptime("13:00", "%H:%M").time(),
                        location="Столовая",
                        duration=40,
                        chat_id=12309876,
                        exact_name_from_table="демов",
                    ),
                ],
            },
            {
                34567890: [
                    {
                        "date_str": "09.10.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time_period_str": "08:40 - 09:50",
                        "duration": "10",
                        "chat_id": "34567890",
                        "exact_name_from_table": "тестова",
                    },
                    {
                        "date_str": "09.10.2025",
                        "admin": "Тестов",
                        "location": "3 этаж 2 корпус",
                        "time_period_str": "09:45 - 09:50",
                        "duration": "10",
                        "chat_id": "34567890",
                        "exact_name_from_table": "тестова",
                    },
                ],
                12309876: [
                    {
                        "date_str": "09.10.2025",
                        "admin": "Дежурный тьютор",
                        "location": "Столовая",
                        "time_period_str": "09:20 - 10:00",
                        "duration": "40",
                        "chat_id": "12309876",
                        "exact_name_from_table": "демов",
                    }
                ],
            },
            1,
        ),
        (
            "2025-10-09 10:00:59.900000",
            {
                "тестова": [
                    ValidDutyRow(
                        date=datetime.strptime("09.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:10", "%H:%M").time(),
                        time_2=datetime.strptime("10:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=40,
                        chat_id=34567890,
                        exact_name_from_table="тестова",
                    ),
                    ValidDutyRow(
                        date=datetime.strptime("09.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("09:40", "%H:%M").time(),
                        time_2=datetime.strptime("09:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=10,
                        chat_id=34567890,
                        exact_name_from_table="тестова",
                    ),
                ],
                "демов": [
                    ValidDutyRow(
                        date=datetime.strptime("09.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("09:20", "%H:%M").time(),
                        time_2=datetime.strptime("10:00", "%H:%M").time(),
                        location="Столовая",
                        duration=40,
                        chat_id=12309876,
                        exact_name_from_table="демов",
                    ),
                ],
            },
            {
                34567890: [
                    {
                        "date_str": "09.10.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time_period_str": "10:10 - 10:50",
                        "duration": "10",
                        "chat_id": "34567890",
                        "exact_name_from_table": "тестова",
                    },
                    {
                        "date_str": "09.10.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time_period_str": "09:40 - 09:50",
                        "duration": "10",
                        "chat_id": "34567890",
                        "exact_name_from_table": "тестова",
                    },
                ],
                12309876: [
                    {
                        "date_str": "09.10.2025",
                        "admin": "Дежурный тьютор",
                        "location": "Столовая",
                        "time_period_str": "08:20 - 09:00",
                        "duration": "40",
                        "chat_id": "12309876",
                        "exact_name_from_table": "демов",
                    }
                ],
            },
            0,
        ),
    ],
)
async def test_notify_15_minutes_before(
    mocker: MockerFixture,
    now,
    actual_data: dict[str, list[ValidDutyRow]],
    sent_reminders_for_test,
    count_number,
):
    with freeze_time(now):
        mocker.patch.object(
            manage_sent_reminders_instance,
            "get_sent_reminders",
            return_value=sent_reminders_for_test,
        )

        mocker.patch.object(
            manage_sent_reminders_instance,
            "add_duty_to_sent_reminders",
            return_value=sent_reminders_for_test,
        )
        notify_mock = mocker.AsyncMock(return_value=True)
        await notify_15_minutes_before(actual_data, notify_mock)
        assert notify_mock.call_count == count_number


@pytest.mark.asyncio
async def test_save_only_successful_notification(mocker):
    mocker.patch.object(
        reminders,
        "prepare_to_notify_in_advance",
        return_value=True,
    )
    manager = mocker.patch.object(reminders, "manage_sent_reminders_instance")
    manager.get_sent_reminders.return_value = {}
    notify = mocker.AsyncMock(side_effect=[False, True])

    first = ValidDutyRow(
        date="2026-10-02",
        time_1="13:10",
        time_2="13:30",
        location="столовая",
        chat_id=111,
        exact_name_from_table="иванов",
    )
    second = first.model_copy(
        update={"chat_id": 222, "exact_name_from_table": "петров"}
    )

    await reminders.notify_15_minutes_before(
        {"иванов": [first], "петров": [second]},
        notify,
    )

    assert [call.args[0] for call in notify.await_args_list] == [111, 222]
    manager.add_duty_to_sent_reminders.assert_called_once_with(222, second)
