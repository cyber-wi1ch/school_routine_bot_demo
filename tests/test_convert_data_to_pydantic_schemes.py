from datetime import datetime

from school_routine_bot.convert_data_to_pydantic_schemes import (
    convert_data_to_pydantic_schemes,
)
from school_routine_bot.pydantic_schemes import (
    AvailableDutySlots,
    InvalidDutyRow,
    ValidDutyRow,
)


def test_convert_data_to_pydantic_schemes():
    data = {
        "": [
            {
                "date": "19.09.2025",
                "admin": "Тестов",
                "location": "2 этаж 2 корпус ",
                "time": "10:40 - 10:50",
                "duration": "20",
                "exact_name_from_table": "",
            },
            {
                "date": "09.09.2025",
                "admin": "Тестов",
                "location": "2 этаж 2 корпус ",
                "time": "10:40 - 10:50",
                "user_choice_time": "",
                "duration": "",
                "chat_id": "",
                "name": "",
                "by_father_name": "",
                "exact_name_from_table": "",
            },
            {
                "date": "29.09.2025",
                "admin": "Тестов",
                "location": "2 этаж 2 корпус ",
                "time": "10:40 - 10:50",
                "user_choice_time": "10.00 - 10.20",
                "duration": "20",
                "chat_id": "",
                "name": "",
                "by_father_name": "",
            },
        ],
        "семенов": [
            {
                "date": "19.09.2025",
                "admin": "Тестов",
                "location": "2 этаж 2 корпус ",
                "time": "10:40 - 10:50",
                "user_choice_time": "",
                "duration": "20",
                "chat_id": "123456789",
                "name": "ефрем",
                "by_father_name": "федорович",
                "exact_name_from_table": "семенов е. ф.",
            },
            {
                "date": "29.09.2025",
                "admin": "Тестов",
                "location": "2 этаж 2 корпус ",
                "time": "10:40 - 10:50",
                "user_choice_time": "10.00 - 10.20",
                "duration": "20",
                "chat_id": "123456789",
                "name": "ефрем",
                "by_father_name": "федорович",
                "exact_name_from_table": "семенов е. ф.",
            },
        ],
        "тестенко": [
            {
                "date": "19.09.2025",
                "admin": "Тестов",
                "location": "2 этаж 2 корпус ",
                "time": "10:40 - 10:50",
                "user_choice_time": "10.00 - 10.20",
                "duration": "20",
                "name": "",
                "by_father_name": "",
                "exact_name_from_table": "тестенко",
            }
        ],
    }
    valid_duties, available_duties, invalid_duties = (
        {
            "семенов": [
                ValidDutyRow(
                    date=datetime.strptime("19.09.2025", "%d.%m.%Y").date(),
                    location="2 этаж 2 корпус ",
                    time_1=datetime.strptime("10:40", "%H:%M").time(),
                    time_2=datetime.strptime("10:50", "%H:%M").time(),
                    duration=10,
                    chat_id=123456789,
                    name="ефрем",
                    by_father_name="федорович",
                    exact_name_from_table="семенов е. ф.",
                ),
                ValidDutyRow(
                    date=datetime.strptime("29.09.2025", "%d.%m.%Y").date(),
                    location="2 этаж 2 корпус ",
                    time_1=datetime.strptime("10:40", "%H:%M").time(),
                    time_2=datetime.strptime("10:50", "%H:%M").time(),
                    duration=10,
                    chat_id=123456789,
                    name="ефрем",
                    by_father_name="федорович",
                    exact_name_from_table="семенов е. ф.",
                ),
            ]
        },
        {
            "": [
                AvailableDutySlots(
                    date="19.09.2025", location="2 этаж 2 корпус ", time="10:40 - 10:50"
                ),
                AvailableDutySlots(
                    date="09.09.2025", location="2 этаж 2 корпус ", time="10:40 - 10:50"
                ),
                AvailableDutySlots(
                    date="29.09.2025", location="2 этаж 2 корпус ", time="10:40 - 10:50"
                ),
            ]
        },
        {
            "тестенко": [
                InvalidDutyRow(
                    date="19.09.2025",
                    location="2 этаж 2 корпус ",
                    time="10:40 - 10:50",
                    duration="20",
                    name="",
                    by_father_name="",
                    exact_name_from_table="тестенко",
                )
            ]
        },
    )
    assert convert_data_to_pydantic_schemes(data) == (
        valid_duties,
        available_duties,
        invalid_duties,
    )
