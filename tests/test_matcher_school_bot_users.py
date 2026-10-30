from typing import Literal

import pytest

from school_routine_bot.db_files.db_create import get_session
from school_routine_bot.db_files.db_models import User
from school_routine_bot.matcher_school_bot_users import (
    MatcherSchoolBotUsers,
    cut_the_name_note,
    formate_new_user_data,
    match_initials_with_full_name,
    normalize_the_input,
)


# noinspection PyArgumentList
@pytest.mark.parametrize(
    "people_from_table_with_duty_data, bot_users, messenger_tag, edited_duty_data",
    [
        (
            {
                "тестова": [
                    {
                        "date": "19.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус ",
                        "time": "10:40 - 10:50",
                        "user_choice_time": "10.00 - 10.20",
                        "duration": "20",
                        "exact_name_from_table": "тестова а.с.",
                    }
                ],
                "демов": [
                    {
                        "date": "19.09.2025",
                        "admin": "Дежурный тьютор",
                        "location": "Столовая ",
                        "time": "12:20 - 13:00 ",
                        "user_choice_time": "12.10 - 13.00 ",
                        "duration": "50",
                        "exact_name_from_table": "демов д.г.",
                    }
                ],
            },
            [
                User(
                    surname="выдумкина",
                    name="анна",
                    by_father_name="сергеевна",
                    chat_id=98765432,
                ),
                User(
                    surname="условникова",
                    name="софья",
                    by_father_name="андреевна",
                    chat_id=234567890,
                ),
                User(
                    surname="образов",
                    name="дмитрий",
                    by_father_name="георгиевич",
                    chat_id=987654321,
                ),
            ],
            User.chat_id,
            {
                "тестова": [
                    {
                        "date": "19.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус ",
                        "time": "10:40 - 10:50",
                        "user_choice_time": "10.00 - 10.20",
                        "duration": "20",
                        "exact_name_from_table": "тестова а.с.",
                    }
                ],
                "демов": [
                    {
                        "date": "19.09.2025",
                        "admin": "Дежурный тьютор",
                        "location": "Столовая ",
                        "time": "12:20 - 13:00 ",
                        "user_choice_time": "12.10 - 13.00 ",
                        "duration": "50",
                        "exact_name_from_table": "демов д.г.",
                    }
                ],
            },
        ),
        (
            {
                "тестова": [
                    {
                        "date": "19.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус ",
                        "time": "10:40 - 10:50",
                        "user_choice_time": "10.00 - 10.20",
                        "duration": "20",
                        "exact_name_from_table": "тестова а.с.",
                    },
                    {
                        "date": "20.09.2025",
                        "admin": "Условная",
                        "location": "2 этаж 2 корпус ",
                        "time": "10:40 - 10:50",
                        "user_choice_time": "10.00 - 10.40",
                        "duration": "40",
                        "exact_name_from_table": "тестова а.с.",
                    },
                ],
                "демов": [
                    {
                        "date": "19.09.2025",
                        "admin": "Дежурный тьютор",
                        "location": "Столовая ",
                        "time": "12:20 - 13:00 ",
                        "user_choice_time": "12.10 - 13.00 ",
                        "duration": "50",
                        "exact_name_from_table": "демов д.г.",
                    }
                ],
            },
            [
                User(
                    surname="тестова",
                    name="анна",
                    by_father_name="сергеевна",
                    vk_id=123456789,
                ),
                User(
                    surname="демов",
                    name="сергей",
                    by_father_name="федорович",
                    vk_id=234567890,
                ),
                User(
                    surname="демов",
                    name="дмитрий",
                    by_father_name="георгиевич",
                    vk_id=345678901,
                ),
            ],
            User.vk_id,
            {
                "тестова": [
                    {
                        "date": "19.09.2025",
                        "admin": "Тестов",
                        "location": "2 этаж 2 корпус ",
                        "time": "10:40 - 10:50",
                        "user_choice_time": "10.00 - 10.20",
                        "duration": "20",
                        "chat_id": 123456789,
                        "name": "анна",
                        "by_father_name": "сергеевна",
                        "exact_name_from_table": "тестова а.с.",
                    },
                    {
                        "date": "20.09.2025",
                        "admin": "Условная",
                        "location": "2 этаж 2 корпус ",
                        "time": "10:40 - 10:50",
                        "user_choice_time": "10.00 - 10.40",
                        "duration": "40",
                        "chat_id": 123456789,
                        "name": "анна",
                        "by_father_name": "сергеевна",
                        "exact_name_from_table": "тестова а.с.",
                    },
                ],
                "демов": [
                    {
                        "date": "19.09.2025",
                        "admin": "Дежурный тьютор",
                        "location": "Столовая ",
                        "time": "12:20 - 13:00 ",
                        "user_choice_time": "12.10 - 13.00 ",
                        "duration": "50",
                        "chat_id": 345678901,
                        "name": "дмитрий",
                        "by_father_name": "георгиевич",
                        "exact_name_from_table": "демов д.г.",
                    }
                ],
            },
        ),
    ],
)
def test_add_id_if_match(
    people_from_table_with_duty_data,
    bot_users,
    messenger_tag,
    edited_duty_data,
    session,
):
    for user in bot_users:
        session.add(user)
    session.commit()
    matcher = MatcherSchoolBotUsers.__new__(MatcherSchoolBotUsers)
    matcher.id_tag = messenger_tag
    matcher.users = bot_users
    assert matcher.add_id_if_match(people_from_table_with_duty_data) == edited_duty_data


@pytest.mark.parametrize(
    "test_data, expected",
    [
        ("", ""),
        ("Иван ", "Иван"),
        (" иван ", "иван"),
        (" Иван\t ", "Иван"),
    ],
)
def test_normalize_the_input(test_data, expected):
    assert normalize_the_input(test_data) == expected


def test_cut_the_name_note():
    assert cut_the_name_note("федяинов д.л.") == ["федяинов", "д", "л"]


@pytest.mark.parametrize(
    "test_exact_note, test_dict, expected_bool",
    [
        (
            "макётова алёна.е.",
            {"surname": "макетова", "name": "алена", "by_father_name": "ёремовна"},
            True,
        ),
        (
            "иванова т. ",
            {"surname": "иванова", "name": "татьяна", "by_father_name": "семеновна"},
            True,
        ),
        (
            " радужкина ольга васильевна ",
            {"surname": "радужкина", "name": "ольга", "by_father_name": "васильевна"},
            True,
        ),
        (
            "примеров и. с.",
            {"surname": "примеров", "name": "сергей", "by_father_name": "владимирович"},
            False,
        ),
        (
            "примеров и. с.",
            {"surname": "примеров", "name": "игорь", "by_father_name": "сергеевич"},
            True,
        ),
        (
            "примеров",
            {"surname": "примеров", "name": "сергей", "by_father_name": "владимирович"},
            True,
        ),
        (
            "иванов иван",
            {"name": "иван", "by_father_name": "владимирович", "surname": "вымыслов"},
            False,
        ),
    ],
)
def test_match_initials_with_full_name(test_exact_note, test_dict, expected_bool):
    assert match_initials_with_full_name(test_exact_note, test_dict) == expected_bool


@pytest.mark.parametrize(
    "full_name_str, full_name_dict",
    [
        (
            "макетова алена",
            {"surname": "макетова", "name": "алена", "by_father_name": ""},
        ),
        (
            "иванова-короткова ",
            {"surname": "иванова-короткова", "name": "", "by_father_name": ""},
        ),
        (
            " радужкина\tольга-олеся\tвасильевна ",
            {
                "surname": "радужкина",
                "name": "ольга-олеся",
                "by_father_name": "васильевна",
            },
        ),
        (
            "",
            {"surname": "", "name": "", "by_father_name": ""},
        ),
    ],
)
def test_formate_new_user_data(full_name_str, full_name_dict):
    assert formate_new_user_data(full_name_str) == full_name_dict


# NO USER AT ALL TEST
# noinspection PyArgumentList
@pytest.mark.parametrize(
    "old_user_base, gotten_id, full_person_name, messenger_tag, expected_value, new_user",
    [
        (
            [
                User(
                    surname="тестова",
                    name="анна",
                    by_father_name="сергеевна",
                    vk_id=123456789,
                ),
                User(
                    surname="демов",
                    name="сергей",
                    by_father_name="федорович",
                    vk_id=234567890,
                ),
                User(
                    surname="демов",
                    name="дмитрий",
                    by_father_name="георгиевич",
                    vk_id=345678901,
                ),
            ],
            1074,
            "чичикова марина дмитриевна",
            User.vk_id,
            None,
            User(
                surname="чичикова",
                name="марина",
                by_father_name="дмитриевна",
                vk_id=1074,
            ),
        ),
        (
            [
                User(
                    surname="тестова",
                    name="анна",
                    by_father_name="сергеевна",
                    chat_id=123456789,
                ),
                User(
                    surname="демов",
                    name="сергей",
                    by_father_name="федорович",
                    chat_id=234567890,
                ),
                User(
                    surname="демов",
                    name="дмитрий",
                    by_father_name="георгиевич",
                    chat_id=345678901,
                ),
            ],
            1789,
            "чичикова марина дмитриевна",
            User.chat_id,
            None,
            User(
                surname="чичикова",
                name="марина",
                by_father_name="дмитриевна",
                chat_id=1789,
            ),
        ),
    ],
)
def test_write_full_name_into_user_base__case_no_user(
    old_user_base,
    gotten_id,
    full_person_name,
    messenger_tag,
    expected_value,
    new_user,
    session,
):
    for user in old_user_base:
        session.add(user)
    session.commit()

    matcher = MatcherSchoolBotUsers.__new__(MatcherSchoolBotUsers)
    matcher.id_tag = messenger_tag

    result = matcher.write_full_name_into_user_base(gotten_id, full_person_name)
    assert result is True

    found_user = session.query(User).filter(messenger_tag == gotten_id).first()
    assert new_user.surname == found_user.surname
    assert new_user.name == found_user.name
    assert new_user.by_father_name == found_user.by_father_name
    if messenger_tag == User.vk_id:
        assert new_user.vk_id == found_user.vk_id
        # chat_id остался None
        assert found_user.chat_id is expected_value
    elif messenger_tag == User.chat_id:
        assert new_user.chat_id == found_user.chat_id
        # vk_id остался None
        assert found_user.vk_id is expected_value
    # id присвоен
    assert found_user.id is not expected_value


# NO VK ID TEST
# noinspection PyArgumentList
@pytest.mark.parametrize(
    "old_user_base, gotten_id, full_person_name, messenger_tag",
    [
        (
            [
                User(
                    surname="тестова",
                    name="анна",
                    by_father_name="сергеевна",
                    chat_id=123456789,
                ),
                User(
                    surname="демов",
                    name="сергей",
                    by_father_name="федорович",
                    chat_id=234567890,
                ),
                User(
                    surname="демов",
                    name="дмитрий",
                    by_father_name="георгиевич",
                    chat_id=345678901,
                ),
                User(
                    surname="чичикова",
                    name="марина",
                    by_father_name="дмитриевна",
                    chat_id=1789,
                ),
            ],
            1074,
            "чичикова марина дмитриевна",
            User.vk_id,
        ),
    ],
)
def test_write_full_name_into_user_base__case_no_vk_id(
    old_user_base, gotten_id, full_person_name, messenger_tag, session
):
    for user in old_user_base:
        session.add(user)
    session.commit()

    matcher = MatcherSchoolBotUsers.__new__(MatcherSchoolBotUsers)
    matcher.id_tag = messenger_tag
    result = matcher.write_full_name_into_user_base(gotten_id, full_person_name)
    assert result is True

    # Теперь ищем пользователя по chat_id
    with get_session() as session_2:
        found_user = session_2.query(User).filter(messenger_tag == gotten_id).first()
        assert found_user

    # Проверяем, что у найденного пользователя правильные данные
    assert found_user.surname == "чичикова"
    assert found_user.name == "марина"
    assert found_user.by_father_name == "дмитриевна"
    assert found_user.vk_id == 1074  # добавился новый vk_id
    assert found_user.chat_id == 1789  # остался старый chat_id

    # Проверяем, что пользователь с такой фамилией остался один
    count = session.query(User).filter(User.surname == "чичикова").count()
    assert count == 1


# BOTH IDS WE HAVE TEST
# noinspection PyArgumentList
@pytest.mark.parametrize(
    "old_user_base, gotten_id, full_person_name, messenger_tag",
    [
        (
            [
                User(
                    surname="тестова",
                    name="анна",
                    by_father_name="сергеевна",
                    chat_id=123456789,
                ),
                User(
                    surname="демов",
                    name="сергей",
                    by_father_name="федорович",
                    chat_id=234567890,
                ),
                User(
                    surname="демов",
                    name="дмитрий",
                    by_father_name="георгиевич",
                    chat_id=345678901,
                ),
                User(
                    surname="чичикова",
                    name="марина",
                    by_father_name="дмитриевна",
                    chat_id=1789,
                    vk_id=1074,
                ),
            ],
            1074,
            "чичикова мария дмитриевна",
            User.vk_id,
        ),
        (
            [
                User(
                    surname="тестова",
                    name="анна",
                    by_father_name="сергеевна",
                    chat_id=123456789,
                ),
                User(
                    surname="демов",
                    name="сергей",
                    by_father_name="федорович",
                    chat_id=234567890,
                ),
                User(
                    surname="демов",
                    name="дмитрий",
                    by_father_name="георгиевич",
                    chat_id=345678901,
                ),
                User(
                    surname="чичикова",
                    name="марина",
                    by_father_name="дмитриевна",
                    chat_id=1789,
                    vk_id=1074,
                ),
            ],
            1789,
            "чичикова мария дмитриевна",
            User.chat_id,
        ),
    ],
)
def test_write_full_name_into_user_base__case_both_ids(
    old_user_base, gotten_id, full_person_name, messenger_tag, session
):
    for user in old_user_base:
        session.add(user)
    session.commit()

    matcher = MatcherSchoolBotUsers.__new__(MatcherSchoolBotUsers)
    matcher.id_tag = messenger_tag
    result = matcher.write_full_name_into_user_base(gotten_id, full_person_name)
    assert result is True

    # Теперь ищем пользователя по chat_id
    with get_session() as session_2:
        found_user = session_2.query(User).filter(messenger_tag == gotten_id).first()
        assert found_user

    # Проверяем, что у найденного пользователя правильные данные
    assert found_user.surname == "чичикова"
    assert found_user.name == "мария"  # изменилось имя (было - марина)
    assert found_user.by_father_name == "дмитриевна"
    assert found_user.vk_id == 1074  # должен сохраниться старый vk_id
    assert found_user.chat_id == 1789  # должен сохраниться старый chat_id

    # Проверяем, что пользователь с такой фамилией остался один
    count = session.query(User).filter(User.surname == "чичикова").count()
    assert count == 1


# NO TG ID TEST
# noinspection PyArgumentList
@pytest.mark.parametrize(
    "old_user_base, gotten_id, full_person_name, messenger_tag",
    [
        (
            [
                User(
                    surname="тестова",
                    name="анна",
                    by_father_name="сергеевна",
                    vk_id=123456789,
                ),
                User(
                    surname="демов",
                    name="сергей",
                    by_father_name="федорович",
                    vk_id=234567890,
                ),
                User(
                    surname="демов",
                    name="дмитрий",
                    by_father_name="георгиевич",
                    vk_id=345678901,
                ),
                User(
                    surname="чичикова",
                    name="марина",
                    by_father_name="дмитриевна",
                    vk_id=1074,
                ),
            ],
            1789,
            "чичикова марина дмитриевна",
            User.chat_id,
        ),
    ],
)
def test_write_full_name_into_user_base__case_no_tg_id(
    old_user_base, gotten_id, full_person_name, messenger_tag, session
):
    for user in old_user_base:
        session.add(user)
    session.commit()

    matcher = MatcherSchoolBotUsers.__new__(MatcherSchoolBotUsers)
    matcher.id_tag = messenger_tag
    result = matcher.write_full_name_into_user_base(gotten_id, full_person_name)
    assert result is True

    # Теперь ищем пользователя по chat_id
    with get_session() as session_2:
        found_user = session_2.query(User).filter(messenger_tag == gotten_id).first()
        assert found_user

    # Проверяем, что у найденного пользователя правильные данные
    assert found_user.surname == "чичикова"
    assert found_user.name == "марина"
    assert found_user.by_father_name == "дмитриевна"
    assert found_user.vk_id == 1074  # должен сохраниться старый vk_id
    assert found_user.chat_id == 1789  # добавился новый chat_id

    # Проверяем, что пользователь с такой фамилией остался один
    count = session.query(User).filter(User.surname == "чичикова").count()
    assert count == 1


def test_write_full_name_returns_false_on_commit_error(session, mocker):
    commit = mocker.patch.object(
        type(session),
        "commit",
        side_effect=RuntimeError("Тестовая ошибка сохранения"),
    )
    matcher = MatcherSchoolBotUsers("tg")

    result = matcher.write_full_name_into_user_base(111, "иванов иван иванович")

    commit.assert_called_once_with()
    assert result is False


# noinspection PyArgumentList
@pytest.mark.parametrize("messenger", ["tg", "vk"])
def test_registration_does_not_overwrite_existing_id(
    session, messenger: Literal["tg", "vk"]
):
    user = User(
        surname="иванов",
        name="иван",
        by_father_name="иванович",
        chat_id=111,
        vk_id=222,
    )
    session.add(user)
    session.commit()

    matcher = MatcherSchoolBotUsers(messenger)
    result = matcher.write_full_name_into_user_base(333, "иванов иван иванович")

    session.refresh(user)

    assert result is False
    assert user.chat_id == 111
    assert user.vk_id == 222
    assert session.query(User).count() == 1


# noinspection PyArgumentList
@pytest.mark.parametrize("user_exists", [False, True])
@pytest.mark.parametrize("full_name", ["", " \t\n "])
def test_empty_full_name_does_not_change_users(session, user_exists, full_name):
    if user_exists:
        session.add(
            User(surname="иванов", name="иван", by_father_name="иванович", chat_id=111)
        )
        session.commit()

    matcher = MatcherSchoolBotUsers("tg")
    result = matcher.write_full_name_into_user_base(111, full_name)

    assert result is False

    saved_users = session.query(
        User.surname, User.name, User.by_father_name, User.chat_id
    ).all()
    expected = [("иванов", "иван", "иванович", 111)] if user_exists else []
    assert saved_users == expected
