from datetime import datetime, time, timedelta

import pytest
from freezegun import freeze_time

from school_routine_bot.pydantic_schemes import (
    AvailableDutySlots,
    InvalidDutyRow,
    ValidDutyRow,
)
from school_routine_bot.school_scheduler import (
    assemble_duty_info_for_each_person,
    cut_time_points_out_of_str,
    define_duration,
    filter_duties,
    get_available_ids_and_not_bot_users,
    get_next_datetime,
    get_person_id,
    handle_not_standard_time_points,
    handle_the_russian_letter_e_with_dots_in_name,
    make_the_duty_data_info_actual,
    sort_data_by_certain_time_for_av_duty_slots_and_invalid_data,
    sort_data_by_certain_time_period,
    turn_duty_into_message,
    turn_empty_duty_slots_into_message,
    turn_english_alike_letters_into_russian,
    turn_names_into_column,
    upper_first_letter,
    upper_first_letters_in_complex_names,
)


def get_tomorrow() -> str:
    return (datetime.today().date() + timedelta(days=1)).strftime("%d.%m.%Y")


def get_today() -> str:
    return datetime.today().date().strftime("%d.%m.%Y")


def test_upper_first_letter():
    name = "вымыслов"
    assert upper_first_letter(name) == "Вымыслов"


@pytest.mark.parametrize(
    "name, handled_name",
    [
        (" Фёдоров Ёрём Семёнович", "федоров ерем семенович"),
        (" Федоров Ёрём", "федоров ерем"),
        (" Фёдоров ", "федоров"),
        ("Ёёшта Артём Ерёмович ", "еешта артем еремович"),
    ],
)
def test_handle_the_russian_letter_e_with_dots_in_name(name, handled_name):
    assert handle_the_russian_letter_e_with_dots_in_name(name) == handled_name


def test_turn_duty_into_message():
    duty: ValidDutyRow = ValidDutyRow(
        date=datetime.strptime("19.09.2025", "%d.%m.%Y").date(),
        time_1=datetime.strptime("10:40", "%H:%M").time(),
        time_2=datetime.strptime("10:50", "%H:%M").time(),
        location="2 этаж 2 корпус ",
        duration=10,
        chat_id=123456789,
        exact_name_from_table="выдумкина анна сергеевна",
        name="анна",
        by_father_name="сергеевна",
    )

    assert turn_duty_into_message(duty) == (
        "Информация о Вашем дежурстве, Анна Сергеевна📝:\n"
        "\n"
        "📅Дата - <u>19.09.2025</u>\n"
        "⏰Время - <b><u>10:40 - 10:50</u></b>\n"
        "🏫Место - <b><u>2 этаж 2 корпус </u></b>\n"
        "⏳Длительность - <u>10 минут</u>\n"
        "\n"
        "<i>❕Если есть вопросы по дежурству, "
        "обратитесь к ответственному за расписание.</i>"
    )


@pytest.mark.parametrize(
    "time_point, correct_time_point",
    [
        ("12:60", "13:00"),
        ("13:78", "14:18"),
        ("13:59", "13:59"),
        ("14:80", "15:20"),
        ("15:94", "16:34"),
        ("", ""),
    ],
)
def test_handle_not_standard_time_points(time_point, correct_time_point):
    assert handle_not_standard_time_points(time_point) == correct_time_point


@pytest.mark.parametrize(
    "time_point",
    [
        "12:600",
        "23:78",
        "24:01",
        "113:159",
        "14:8012",
        "1565:94",
    ],
)
def test_handle_not_standard_time_points_value_error(time_point):
    with pytest.raises(ValueError) as e:
        handle_not_standard_time_points(time_point)
    assert "Time input is incorrect. Check the Google table worksheet, please." in str(
        e
    )


def test_cut_time_points_out_of_str():
    assert cut_time_points_out_of_str("c 10:00 - 10.30") == ("10:00", "10:30")


def test_define_duration():
    assert define_duration("08:00", "09:01") == "61"


@pytest.mark.parametrize(
    "not_actual_data, actual_data",
    [
        (
            {
                "тестова": [
                    {
                        "date": "19.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time": "10:40 - 10:50",
                        "user_choice_time": "10.00 - 10.20",
                        "duration": "10",
                    },
                    {
                        "date": "20.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time": "10:40 - 10:50",
                        "user_choice_time": "",
                        "duration": "10",
                    },
                ],
                "демов": [
                    {
                        "date": "19.09.2025",
                        "admin": "Дежурный тьютор",
                        "location": "Столовая",
                        "time": "12:20 - 13:00",
                        "user_choice_time": "12.10 - 13.00",
                        "duration": "40",
                    }
                ],
            },
            {
                "тестова": [
                    {
                        "date": "19.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time": "10:00 - 10:20",
                        "duration": "20",
                    },
                    {
                        "date": "20.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус",
                        "time": "10:40 - 10:50",
                        "duration": "10",
                        "user_choice_time": "",
                    },
                ],
                "демов": [
                    {
                        "date": "19.09.2025",
                        "admin": "Дежурный тьютор",
                        "location": "Столовая",
                        "time": "12:10 - 13:00",
                        "duration": "50",
                    }
                ],
            },
        ),
    ],
)
def test_make_the_duty_info_actual(not_actual_data, actual_data):
    assert make_the_duty_data_info_actual(not_actual_data) == actual_data


@pytest.mark.parametrize(
    "actual_data, sorted_data_for_tomorrow",
    [
        (
            {
                "тестова": [
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:00", "%H:%M").time(),
                        time_2=datetime.strptime("10:20", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=20,
                        chat_id=123456789,
                        exact_name_from_table="тестова",
                    ),
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:40", "%H:%M").time(),
                        time_2=datetime.strptime("10:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=10,
                        chat_id=123456789,
                        exact_name_from_table="тестова",
                    ),
                ],
                "демов": [
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("16:00", "%H:%M").time(),
                        time_2=datetime.strptime("18:00", "%H:%M").time(),
                        location="Столовая",
                        duration=30,
                        chat_id=987654321,
                        exact_name_from_table="демов",
                    ),
                ],
                "демова": [
                    ValidDutyRow(
                        date=datetime.strptime("30.09.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:00", "%H:%M").time(),
                        time_2=datetime.strptime("10:20", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=20,
                        chat_id=124,
                        exact_name_from_table="демова",
                    ),
                ],
            },
            {
                "тестова": [
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:00", "%H:%M").time(),
                        time_2=datetime.strptime("10:20", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=20,
                        chat_id=123456789,
                        exact_name_from_table="тестова",
                    ),
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:40", "%H:%M").time(),
                        time_2=datetime.strptime("10:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=10,
                        chat_id=123456789,
                        exact_name_from_table="тестова",
                    ),
                ],
                "демов": [
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("16:00", "%H:%M").time(),
                        time_2=datetime.strptime("18:00", "%H:%M").time(),
                        location="Столовая",
                        duration=30,
                        chat_id=987654321,
                        exact_name_from_table="демов",
                    ),
                ],
            },
        ),
    ],
)
def test_sort_data_by_certain_time_period(
    actual_data: dict[str, list[ValidDutyRow]],
    sorted_data_for_tomorrow: dict[str, list[ValidDutyRow]],
):
    assert sort_data_by_certain_time_period(actual_data) == sorted_data_for_tomorrow


@pytest.mark.parametrize(
    "available_duty_slots, invalid_data, "
    "sorted_empty_duty_info, sorted_invalid_duty_info",
    [
        (
            {
                "": [
                    AvailableDutySlots(
                        date=get_tomorrow(),
                        location="2 этаж 1 корпус",
                        time="с 09:45-09:55",
                    ),
                    AvailableDutySlots(
                        date="12.01.2026",
                        location="2 этаж 1 корпус",
                        time="с 09:45-09:55",
                    ),
                ]
            },
            {
                "демова": [
                    InvalidDutyRow(
                        date="30.09.2025",
                        time="10.00 - 10.20",
                        location="2 этаж 2 корпус",
                        duration="20",
                        chat_id=None,
                        exact_name_from_table="демова а. ю.",
                        name=None,
                        by_father_name=None,
                    )
                ],
                "демов": [
                    InvalidDutyRow(
                        date=get_tomorrow(),
                        time="10.00 - 10.20",
                        location="2 этаж 2 корпус",
                        duration="20",
                        chat_id=None,
                        exact_name_from_table="демов а. ю.",
                        name=None,
                        by_father_name=None,
                    )
                ],
            },
            {
                "": [
                    AvailableDutySlots(
                        date=get_tomorrow(),
                        location="2 этаж 1 корпус",
                        time="с 09:45-09:55",
                    )
                ]
            },
            {
                "демов": [
                    InvalidDutyRow(
                        date=get_tomorrow(),
                        time="10.00 - 10.20",
                        location="2 этаж 2 корпус",
                        duration="20",
                        chat_id=None,
                        exact_name_from_table="демов а. ю.",
                        name=None,
                        by_father_name=None,
                    )
                ]
            },
        )
    ],
)
def test_sort_data_by_certain_time_for_av_duty_slots_and_invalid_data(
    available_duty_slots: dict[str, list[AvailableDutySlots]],
    invalid_data: dict[str, list[InvalidDutyRow]],
    sorted_empty_duty_info: dict[str, list[AvailableDutySlots]],
    sorted_invalid_duty_info: dict[str, list[InvalidDutyRow]],
):
    assert sort_data_by_certain_time_for_av_duty_slots_and_invalid_data(
        available_duty_slots, invalid_data
    ) == (sorted_empty_duty_info, sorted_invalid_duty_info)


@pytest.mark.parametrize(
    "valid_duty_data, invalid_duty_data, ids_and_not_bot_users",
    [
        (
            {
                "тестова и. ю.": [
                    ValidDutyRow(
                        date=datetime.strptime("19.09.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:00", "%H:%M").time(),
                        time_2=datetime.strptime("10:20", "%H:%M").time(),
                        location="2 этаж 2 корпус ",
                        duration=20,
                        chat_id=123456789,
                        exact_name_from_table="тестова и. ю.",
                    ),
                    ValidDutyRow(
                        date=datetime.strptime("20.09.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:40", "%H:%M").time(),
                        time_2=datetime.strptime("10:50", "%H:%M").time(),
                        location="2 этаж 2 корпус ",
                        duration=10,
                        chat_id=123456789,
                        exact_name_from_table="тестова и. ю.",
                    ),
                ],
                "демов": [
                    ValidDutyRow(
                        date=datetime.strptime("19.09.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("12:10", "%H:%M").time(),
                        time_2=datetime.strptime("13:00", "%H:%M").time(),
                        location="Столовая ",
                        duration=50,
                        chat_id=987654321,
                        exact_name_from_table="демов",
                    ),
                ],
            },
            {
                "демова": [
                    InvalidDutyRow(
                        date="30.09.2025",
                        time="10.00 - 10.20",
                        location="2 этаж 2 корпус",
                        duration="20",
                        chat_id=None,
                        exact_name_from_table="демова а. ю.",
                        name=None,
                        by_father_name=None,
                    )
                ],
            },
            ({123456789, 987654321}, ["Демова А. Ю."]),
        ),
    ],
)
def test_get_available_ids_and_not_bot_users(
    valid_duty_data: dict[str, list[ValidDutyRow]],
    invalid_duty_data: dict[str, list[InvalidDutyRow]],
    ids_and_not_bot_users: tuple[set, list],
):
    assert (
        get_available_ids_and_not_bot_users(valid_duty_data, invalid_duty_data)
        == ids_and_not_bot_users
    )


@pytest.mark.parametrize(
    "person_id, duty_data, message",
    [
        (
            123456789,
            {
                "тестова": [
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:00", "%H:%M").time(),
                        time_2=datetime.strptime("10:20", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=20,
                        chat_id=123456789,
                        exact_name_from_table="тестова",
                        name="ирина",
                        by_father_name="владимировна",
                    ),
                ],
                "демов": [
                    ValidDutyRow(
                        date=datetime.strptime(get_today(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("17:30", "%H:%M").time(),
                        time_2=datetime.strptime("18:00", "%H:%M").time(),
                        location="Столовая",
                        duration=30,
                        chat_id=987654321,
                        exact_name_from_table="демов и.",
                        name="игорь",
                        by_father_name="",
                    ),
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:30", "%H:%M").time(),
                        time_2=datetime.strptime("11:00", "%H:%M").time(),
                        location="Коридор",
                        duration=30,
                        chat_id=987654321,
                        exact_name_from_table="демов и.",
                        name="игорь",
                        by_father_name="",
                    ),
                ],
                "демова": [
                    ValidDutyRow(
                        date=datetime.strptime("30.09.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:00", "%H:%M").time(),
                        time_2=datetime.strptime("10:20", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=20,
                        chat_id=124,
                        exact_name_from_table="демова",
                    ),
                ],
            },
            [
                f"Информация о Вашем дежурстве, Ирина Владимировна📝:\n"
                "\n"
                f"📅Дата - <u>{get_tomorrow()}</u>\n"
                f"⏰Время - <b><u>10:00 - 10:20</u></b>\n"
                f"🏫Место - <b><u>2 этаж 2 корпус</u></b>\n"
                f"⏳Длительность - <u>20 минут</u>\n"
                "\n"
                "<i>❕Если есть вопросы по дежурству, "
                "обратитесь к ответственному за расписание.</i>"
            ],
        ),
        (
            987654321,
            {
                "тестова": [
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:00", "%H:%M").time(),
                        time_2=datetime.strptime("10:00", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=20,
                        chat_id=123456789,
                        exact_name_from_table="тестова",
                        name="ирина",
                        by_father_name="владимировна",
                    ),
                ],
                "демов": [
                    ValidDutyRow(
                        date=datetime.strptime(get_today(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("17:30", "%H:%M").time(),
                        time_2=datetime.strptime("18:00", "%H:%M").time(),
                        location="Столовая",
                        duration=30,
                        chat_id=987654321,
                        exact_name_from_table="демов и.",
                        name="игорь",
                        by_father_name="",
                    ),
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:30", "%H:%M").time(),
                        time_2=datetime.strptime("11:00", "%H:%M").time(),
                        location="Коридор",
                        duration=30,
                        chat_id=987654321,
                        exact_name_from_table="демов и.",
                        name="игорь",
                        by_father_name="",
                    ),
                ],
                "демова": [
                    ValidDutyRow(
                        date=datetime.strptime("30.09.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:00", "%H:%M").time(),
                        time_2=datetime.strptime("10:20", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=20,
                        chat_id=124,
                        exact_name_from_table="демова",
                    ),
                ],
            },
            [
                f"Информация о Вашем дежурстве, Игорь 📝:\n"
                "\n"
                f"📅Дата - <u>{get_today()}</u>\n"
                f"⏰Время - <b><u>17:30 - 18:00</u></b>\n"
                f"🏫Место - <b><u>Столовая</u></b>\n"
                f"⏳Длительность - <u>30 минут</u>\n"
                "\n"
                "<i>❕Если есть вопросы по дежурству, "
                "обратитесь к ответственному за расписание.</i>",
                f"Информация о Вашем дежурстве, Игорь 📝:\n"
                "\n"
                f"📅Дата - <u>{get_tomorrow()}</u>\n"
                f"⏰Время - <b><u>10:30 - 11:00</u></b>\n"
                f"🏫Место - <b><u>Коридор</u></b>\n"
                f"⏳Длительность - <u>30 минут</u>\n"
                "\n"
                "<i>❕Если есть вопросы по дежурству, "
                "обратитесь к ответственному за расписание.</i>",
            ],
        ),
    ],
)
def test_assemble_duty_info_for_each_person(
    person_id: int, duty_data: dict[str, list[ValidDutyRow]], message
):
    assert assemble_duty_info_for_each_person(person_id, duty_data) == message


def test_turn_empty_duty_slots_into_message():
    empty_duties: list[AvailableDutySlots] = [
        AvailableDutySlots(
            date="12.10.2025", location="2 этаж 1 корпус", time="с 09:45-09:55"
        ),
        AvailableDutySlots(
            date="12.10.2025", location="3 этаж 1 корпус", time="с 13:00-13:35"
        ),
        AvailableDutySlots(
            date="12.10.2025", location="4 этаж 1 корпус", time="с 10:15-10:50"
        ),
    ]

    message = (
        "<b><u>12.10.2025</u></b>\n"
        "\n"
        "<b>с 09:45-09:55</b> <i>2 этаж 1 корпус</i>\n"
        "<b>с 13:00-13:35</b> <i>3 этаж 1 корпус</i>\n"
        "<b>с 10:15-10:50</b> <i>4 этаж 1 корпус</i>\n"
    )
    assert turn_empty_duty_slots_into_message(empty_duties) == message


def test_turn_names_into_column():
    names = ["Демова", "Макетов", "Образов", "Макетова"]
    column = "Демова\nМакетов\nОбразов\nМакетова\n"
    assert turn_names_into_column(names) == column


@pytest.mark.parametrize(
    "person_name, duty_data, chat_id",
    [
        (
            "тестова",
            {
                "тестова": [
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:00", "%H:%M").time(),
                        time_2=datetime.strptime("10:00", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=20,
                        chat_id=123456789,
                        exact_name_from_table="тестова",
                        name="ирина",
                        by_father_name="владимировна",
                    ),
                ],
                "демов": [
                    ValidDutyRow(
                        date=datetime.strptime(get_today(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("17:30", "%H:%M").time(),
                        time_2=datetime.strptime("18:00", "%H:%M").time(),
                        location="Столовая",
                        duration=30,
                        chat_id=987654321,
                        exact_name_from_table="демов и.",
                        name="игорь",
                        by_father_name="",
                    ),
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:30", "%H:%M").time(),
                        time_2=datetime.strptime("11:00", "%H:%M").time(),
                        location="Коридор",
                        duration=30,
                        chat_id=987654321,
                        exact_name_from_table="демов и.",
                        name="игорь",
                        by_father_name="",
                    ),
                ],
                "демова": [
                    ValidDutyRow(
                        date=datetime.strptime("30.09.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:00", "%H:%M").time(),
                        time_2=datetime.strptime("10:20", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=20,
                        chat_id=124,
                        exact_name_from_table="демова",
                    ),
                ],
            },
            123456789,
        ),
        (
            "демов",
            {
                "тестова": [
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:00", "%H:%M").time(),
                        time_2=datetime.strptime("10:00", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=20,
                        chat_id=123456789,
                        exact_name_from_table="тестова",
                        name="ирина",
                        by_father_name="владимировна",
                    ),
                ],
                "демов": [
                    ValidDutyRow(
                        date=datetime.strptime(get_today(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("17:30", "%H:%M").time(),
                        time_2=datetime.strptime("18:00", "%H:%M").time(),
                        location="Столовая",
                        duration=30,
                        chat_id=987654321,
                        exact_name_from_table="демов и.",
                        name="игорь",
                        by_father_name="",
                    ),
                    ValidDutyRow(
                        date=datetime.strptime(get_tomorrow(), "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:30", "%H:%M").time(),
                        time_2=datetime.strptime("11:00", "%H:%M").time(),
                        location="Коридор",
                        duration=30,
                        chat_id=987654321,
                        exact_name_from_table="демов и.",
                        name="игорь",
                        by_father_name="",
                    ),
                ],
                "демова": [
                    ValidDutyRow(
                        date=datetime.strptime("30.09.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("10:00", "%H:%M").time(),
                        time_2=datetime.strptime("10:20", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=20,
                        chat_id=124,
                        exact_name_from_table="демова",
                    ),
                ],
            },
            987654321,
        ),
    ],
)
def test_get_person_id(
    person_name, duty_data: dict[str, list[ValidDutyRow]], chat_id: int
):
    assert get_person_id(person_name, duty_data) == chat_id


@freeze_time("2000-05-10 13:00:00")
def test_get_next_datetime():
    assert get_next_datetime(time(17)) == datetime(2000, 5, 10, 17)
    assert get_next_datetime(
        time(10), related_to=datetime(2020, 5, 10, hour=1, minute=10)
    ) == datetime(2020, 5, 10, hour=10)
    assert get_next_datetime(
        time(10), related_to=datetime(2020, 5, 10, hour=11, minute=10)
    ) == datetime(2020, 5, 11, hour=10)

    assert get_next_datetime(
        time(10), datetime(2000, 5, 10, hour=1, minute=10), 2
    ) == datetime(2000, 5, 12, 10)


def test_filter_duties__empty_data():
    now = datetime.now()
    assert filter_duties({}, from_time=now, to_time=now) == {}
    assert filter_duties({"kinda_name": []}, from_time=now, to_time=now) == {}


@pytest.mark.parametrize(
    "initial_data, from_time, to_time, filtered_data",
    [
        (
            {
                "q": [
                    ValidDutyRow(
                        date=datetime.strptime("20.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("14:40", "%H:%M").time(),
                        time_2=datetime.strptime("14:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=10,
                        chat_id=124,
                        exact_name_from_table="демова",
                    ),
                ]
            },
            datetime(2025, 10, 20, 15),
            datetime(2025, 10, 20, 16),
            {},
        ),
        (
            {
                "q": [
                    ValidDutyRow(
                        date=datetime.strptime("20.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("14:40", "%H:%M").time(),
                        time_2=datetime.strptime("14:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=10,
                        chat_id=124,
                        exact_name_from_table="демова",
                    ),
                ]
            },
            datetime(2025, 10, 20, 14, 50),
            datetime(2025, 10, 20, 16),
            {},
        ),
        (
            {
                "q": [
                    ValidDutyRow(
                        date=datetime.strptime("20.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("14:40", "%H:%M").time(),
                        time_2=datetime.strptime("14:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=10,
                        chat_id=124,
                        exact_name_from_table="демова",
                    ),
                ]
            },
            datetime(2025, 10, 20, 14, 30),
            datetime(2025, 10, 20, 16),
            {
                "q": [
                    ValidDutyRow(
                        date=datetime.strptime("20.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("14:40", "%H:%M").time(),
                        time_2=datetime.strptime("14:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=10,
                        chat_id=124,
                        exact_name_from_table="демова",
                    ),
                ]
            },
        ),
        (
            {
                "q": [
                    ValidDutyRow(
                        date=datetime.strptime("20.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("14:40", "%H:%M").time(),
                        time_2=datetime.strptime("14:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=10,
                        chat_id=124,
                        exact_name_from_table="демова",
                    ),
                ],
                "w": [
                    ValidDutyRow(
                        date=datetime.strptime("20.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("15:40", "%H:%M").time(),
                        time_2=datetime.strptime("15:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=10,
                        chat_id=124,
                        exact_name_from_table="демова",
                    ),
                ],
            },
            datetime(2025, 10, 20, 14, 30),
            datetime(2025, 10, 20, 15),
            {
                "q": [
                    ValidDutyRow(
                        date=datetime.strptime("20.10.2025", "%d.%m.%Y").date(),
                        time_1=datetime.strptime("14:40", "%H:%M").time(),
                        time_2=datetime.strptime("14:50", "%H:%M").time(),
                        location="2 этаж 2 корпус",
                        duration=10,
                        chat_id=124,
                        exact_name_from_table="демова",
                    ),
                ]
            },
        ),
    ],
)
def test_filter_duties(
    initial_data: dict[str, list[ValidDutyRow]],
    from_time: datetime,
    to_time: datetime,
    filtered_data: dict[str, list[ValidDutyRow]],
):
    assert filter_duties(initial_data, from_time, to_time) == filtered_data


@pytest.mark.parametrize(
    "complex_surname, upper_surname",
    [
        ("архангельский-бажов", "Архангельский-Бажов"),
        ("тестовая-пробная-фантазина", "Тестовая-Пробная-Фантазина"),
        ("выдумкина", "Выдумкина"),
    ],
)
def test_upper_first_letters_in_complex_names(complex_surname, upper_surname):
    assert upper_first_letters_in_complex_names(complex_surname) == upper_surname


def test_turn_english_alike_letters_into_russian():
    assert (
        turn_english_alike_letters_into_russian("Beдёркинa A. B.") == "ведеркина а. в."
    )
