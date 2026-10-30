import pytest

from school_routine_bot.scheduler_organizer import (
    convert_duty_data_to_dict,
    cut_out_the_surname,
    fill_in_gaps_except_for_some_last_cols,
)


@pytest.mark.parametrize(
    "name_from_table, last_name",
    [
        ("", ""),
        (" Bымыслов И.В. ", "вымыслов"),
        ("Вымыслов Иван В. ", "вымыслов"),
        ("Вымыслов Иван Владимирович", "вымыслов"),
        ("Вымыслов", "вымыслов"),
    ],
)
def test_cut_out_the_surname(name_from_table, last_name):
    assert cut_out_the_surname(name_from_table) == last_name


@pytest.mark.parametrize(
    "duty_data_list, duty_data_dict",
    [
        (
            [
                [
                    "19.09.2025",
                    "Тестов",
                    "2 этаж 2 корпус ",
                    "10:40 - 10:50",
                    "10.00 - 10.20",
                    "20",
                    "Тестова Е.И.",
                ],
                [
                    "19.09.2025",
                    "Дежурный тьютор",
                    "Столовая ",
                    "12:20 - 13:00 ",
                    "12.10 - 13.00 ",
                    "50",
                    "Демов И.А.",
                ],
            ],
            {
                "тестова": [
                    {
                        "date": "19.09.2025",
                        "admin": "тестов",
                        "location": "2 этаж 2 корпус",
                        "time": "10:40 - 10:50",
                        "user_choice_time": "10.00 - 10.20",
                        "duration": "20",
                        "exact_name_from_table": "тестова е.и.",
                    }
                ],
                "демов": [
                    {
                        "date": "19.09.2025",
                        "admin": "дежурный тьютор",
                        "location": "столовая",
                        "time": "12:20 - 13:00",
                        "user_choice_time": "12.10 - 13.00",
                        "duration": "50",
                        "exact_name_from_table": "демов и.а.",
                    }
                ],
            },
        ),
        (
            [
                [
                    "19.09.2025",
                    "Тестов",
                    "2 этаж 2 корпус ",
                    "10:40 - 10:50",
                    "10.00 - 10.20",
                    "20",
                ],
                [
                    "19.09.2025",
                    "Дежурный тьютор",
                    "Столовая ",
                    "12:20 - 13:00 ",
                    "12.10 - 13.00 ",
                    "50",
                ],
            ],
            {
                "": [
                    {
                        "date": "19.09.2025",
                        "admin": "тестов",
                        "location": "2 этаж 2 корпус",
                        "time": "10:40 - 10:50",
                        "user_choice_time": "10.00 - 10.20",
                        "duration": "20",
                        "exact_name_from_table": "",
                    },
                    {
                        "date": "19.09.2025",
                        "admin": "дежурный тьютор",
                        "location": "столовая",
                        "time": "12:20 - 13:00",
                        "user_choice_time": "12.10 - 13.00",
                        "duration": "50",
                        "exact_name_from_table": "",
                    },
                ]
            },
        ),
    ],
)
def test_convert_duty_data_to_dict(duty_data_list: list[list], duty_data_dict: dict):
    assert convert_duty_data_to_dict(duty_data_list) == duty_data_dict


@pytest.mark.parametrize(
    "table_with_blanks, table_without_unnecessary_blanks",
    [
        (
            [
                [
                    "19.09.2025",
                    "Тестов",
                    "Столовая ",
                    "12:20 - 13:00 ",
                    "",
                    "40",
                    "Примерова",
                ],
                ["", "", "", "", "12.10 - 13.00 ", "50", "Демов"],
                ["", "", "2 этаж 2 корпус ", "10:40 - 10:50", "", "", ""],
                ["", "", "", "", "10.00 - 10.20", "20", "Тестова"],
            ],
            [
                [
                    "19.09.2025",
                    "Тестов",
                    "Столовая ",
                    "12:20 - 13:00 ",
                    "",
                    "40",
                    "Примерова",
                ],
                [
                    "19.09.2025",
                    "Тестов",
                    "Столовая ",
                    "12:20 - 13:00 ",
                    "12.10 - 13.00 ",
                    "50",
                    "Демов",
                ],
                [
                    "19.09.2025",
                    "Тестов",
                    "2 этаж 2 корпус ",
                    "10:40 - 10:50",
                    "",
                    "",
                    "",
                ],
                [
                    "19.09.2025",
                    "Тестов",
                    "2 этаж 2 корпус ",
                    "10:40 - 10:50",
                    "10.00 - 10.20",
                    "20",
                    "Тестова",
                ],
            ],
        ),
    ],
)
def test_fill_in_gaps_except_for_some_last_cols(
    table_with_blanks, table_without_unnecessary_blanks
):
    assert (
        fill_in_gaps_except_for_some_last_cols(table_with_blanks)
        == table_without_unnecessary_blanks
    )
