from datetime import datetime

import pytest
from freezegun import freeze_time

from school_routine_bot.duty_utils_for_bot_clients import (
    format_actual_duty_button_text,
    make_actual_duty_message_for_person,
    make_message_for_actual_duties_button,
)
from school_routine_bot.pydantic_schemes import ValidDutyRow


def test_make_message_for_actual_duties_button():
    assert make_message_for_actual_duties_button(
        "25.06.2025", "Столовая", "12:00 - 12:30"
    ) == (
        "\n🟢 <b>ДАТА</b> - <u>25.06.2025</u>,\n"
        "<b>МЕСТО</b> - <u>Столовая</u>,\n"
        "<b>ВРЕМЯ</b> - <u>12:00 - 12:30</u>.\n\n"
    )


@freeze_time("2025-10-28 11:48:10.909", tick=True)
@pytest.mark.parametrize(
    "person, chat_id, duty_data, message",
    [
        (
            "марканян",
            56709855,
            {
                "тестова": [
                    ValidDutyRow(
                        date=datetime.strptime("27.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:40", "%H:%M").time(),
                        time_2=datetime.strptime("10:50", "%H:%M").time(),
                        location="2 этаж 2 корпус ",
                        duration=10,
                        chat_id=56789034,
                        exact_name_from_table="тестова а.с.",
                    ),
                ],
                "демов": [
                    ValidDutyRow(
                        date=datetime.strptime("30.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("12:20", "%H:%M").time(),
                        time_2=datetime.strptime("13:00", "%H:%M").time(),
                        location="2 этаж 2 корпус ",
                        duration=40,
                        chat_id=123,
                        exact_name_from_table="демов д.г.",
                    ),
                ],
            },
            "",
        ),
        (
            "тестова",
            56789034,
            {
                "тестова": [
                    ValidDutyRow(
                        date=datetime.strptime("29.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("12:40", "%H:%M").time(),
                        time_2=datetime.strptime("12:50", "%H:%M").time(),
                        location="2 этаж 2 корпус ",
                        duration=10,
                        chat_id=56789034,
                        exact_name_from_table="тестова а.с.",
                    ),
                    ValidDutyRow(
                        date=datetime.strptime("28.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("12:20", "%H:%M").time(),
                        time_2=datetime.strptime("13:00", "%H:%M").time(),
                        location="Столовая ",
                        duration=40,
                        chat_id=56789034,
                        exact_name_from_table="тестова а.с.",
                    ),
                ]
            },
            "\n🟢 <b>ДАТА</b> - <u>28.10.2025</u>,\n"
            "<b>МЕСТО</b> - <u>Столовая </u>,\n"
            "<b>ВРЕМЯ</b> - <u>12:20 - 13:00</u>.\n\n"
            "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
            "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
            "<b>ВРЕМЯ</b> - <u>12:40 - 12:50</u>.\n\n",
        ),
        (
            "тестова",
            23456782,
            {
                "тестова": [
                    ValidDutyRow(
                        date=datetime.strptime("30.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:40", "%H:%M").time(),
                        time_2=datetime.strptime("10:50", "%H:%M").time(),
                        location="2 этаж 2 корпус ",
                        duration=10,
                        chat_id=56789034,
                        exact_name_from_table="тестова а.с.",
                    ),
                    ValidDutyRow(
                        date=datetime.strptime("29.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("12:20", "%H:%M").time(),
                        time_2=datetime.strptime("13:00", "%H:%M").time(),
                        location="Столовая ",
                        duration=10,
                        chat_id=23456782,
                        exact_name_from_table="тестова д.г.",
                    ),
                ]
            },
            "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
            "<b>МЕСТО</b> - <u>Столовая </u>,\n"
            "<b>ВРЕМЯ</b> - <u>12:20 - 13:00</u>.\n\n",
        ),
        (
            "тестова",
            56789034,
            {
                "тестова": [
                    ValidDutyRow(
                        date=datetime.strptime("29.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:40", "%H:%M").time(),
                        time_2=datetime.strptime("10:50", "%H:%M").time(),
                        location="2 этаж 2 корпус ",
                        duration=10,
                        chat_id=56789034,
                        exact_name_from_table="тестова а.с.",
                    ),
                ],
                "демов": [
                    ValidDutyRow(
                        date=datetime.strptime("29.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("12:20", "%H:%M").time(),
                        time_2=datetime.strptime("13:00", "%H:%M").time(),
                        location="Столовая ",
                        duration=40,
                        chat_id=123,
                        exact_name_from_table="демов д.г.",
                    ),
                ],
            },
            "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
            "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
            "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n",
        ),
    ],
)
def test_make_actual_duty_message_for_person(
    person, chat_id: int, duty_data: dict[str, list[ValidDutyRow]], message
):
    assert make_actual_duty_message_for_person(person, duty_data, chat_id) == message


def test_format_actual_duty_button_text():
    initial_message = (
        "<i>(Из листа таблицы 'Запись на дежурства')</i>\n "
        "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
        "<b>МЕСТО</b> - <u>2 этаж 2 корпус</u>,\n"
        "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n"
    )
    expected_message = (
        "⏱️Вы дежурите:\n\n "
        "<i>(Из листа таблицы 'Запись на дежурства')</i>\n "
        "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
        "<b>МЕСТО</b> - <u>2 этаж 2 корпус</u>,\n"
        "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n"
    )

    assert format_actual_duty_button_text(initial_message) == expected_message


# IF THERE ARE TWO SHEETS
# @pytest.mark.parametrize(
#     "initial_duty_message, final_duty_message",
#     [
#         (
#             (
#                 "<i>(Из листа таблицы 'Дежурства на ВП')</i>\n "
#                 "<i>(Из листа таблицы 'Запись на дежурства')</i>\n"
#                 "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
#                 "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
#                 "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n"
#             ),
#             (
#                 "⏱️Вы дежурите:\n\n"
#                 "  <i>(Из листа таблицы 'Запись на дежурства')</i>\n"
#                 "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
#                 "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
#                 "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n"
#             ),
#         ),
#         (
#             (
#                 "<i>(Из листа таблицы 'Дежурства на ВП')</i>\n "
#                 "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
#                 "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
#                 "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n"
#                 "<i>(Из листа таблицы 'Запись на дежурства')</i>\n "
#             ),
#             (
#                 "⏱️Вы дежурите:\n\n"
#                 " <i>(Из листа таблицы 'Дежурства на ВП')</i>\n "
#                 "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
#                 "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
#                 "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n "
#             ),
#         ),
#         (
#             (
#                 "<i>(Из листа таблицы 'Запись на дежурства')</i>\n "
#                 "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
#                 "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
#                 "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n"
#                 "<i>(Из листа таблицы 'Дежурства на ВП')</i>\n "
#             ),
#             (
#                 "⏱️Вы дежурите:\n\n"
#                 " <i>(Из листа таблицы 'Запись на дежурства')</i>\n "
#                 "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
#                 "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
#                 "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n "
#             ),
#         ),
#         (
#             (
#                 "<i>(Из листа таблицы 'Запись на дежурства')</i>\n "
#                 "<i>(Из листа таблицы 'Дежурства на ВП')</i>\n"
#                 "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
#                 "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
#                 "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n"
#             ),
#             (
#                 "⏱️Вы дежурите:\n\n"
#                 "  <i>(Из листа таблицы 'Дежурства на ВП')</i>\n"
#                 "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
#                 "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
#                 "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n"
#             ),
#         ),
#         (
#             (
#                 "<i>(Из листа таблицы 'Запись на дежурства')</i>\n "
#                 "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
#                 "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
#                 "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n"
#                 "<i>(Из листа таблицы 'Дежурства на ВП')</i>\n"
#                 "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
#                 "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
#                 "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n"
#             ),
#             (
#                 "⏱️Вы дежурите:\n\n"
#                 " <i>(Из листа таблицы 'Запись на дежурства')</i>\n "
#                 "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
#                 "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
#                 "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n"
#                 "<i>(Из листа таблицы 'Дежурства на ВП')</i>\n"
#                 "\n🟢 <b>ДАТА</b> - <u>29.10.2025</u>,\n"
#                 "<b>МЕСТО</b> - <u>2 этаж 2 корпус </u>,\n"
#                 "<b>ВРЕМЯ</b> - <u>10:40 - 10:50</u>.\n\n"
#             ),
#         ),
#     ],
# )
# def test_format_actual_duty_button_text(initial_duty_message, final_duty_message):
#     assert format_actual_duty_button_text(initial_duty_message) == final_duty_message
