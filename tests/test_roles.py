import pytest

from school_routine_bot.db_files.db_models import LateCatcher, User
from school_routine_bot.roles import (
    LATE_CATCHER_ADDED_RESULT,
    LATE_CATCHER_REMOVED_RESULT,
    UserMessengerIds,
    add_late_catcher_by_full_name,
    get_late_catchers_list,
    get_user_id_by_messenger_id,
    get_user_messenger_ids_by_full_name,
    remove_late_catcher_by_full_name,
)


@pytest.fixture
def user_factory(session):
    # noinspection PyArgumentList
    def create_user(
        surname="иванов",
        name="иван",
        by_father_name="иванович",
        chat_id=12345,
        vk_id=None,
    ):
        user = User(
            surname=surname,
            name=name,
            by_father_name=by_father_name,
            chat_id=chat_id,
            vk_id=vk_id,
        )
        session.add(user)
        session.commit()
        return user

    return create_user


def add_late_catcher_to_session(session, user):
    late_catcher = LateCatcher()
    late_catcher.id = user.id
    session.add(late_catcher)
    session.commit()
    return late_catcher


@pytest.mark.parametrize(
    "full_name, by_father_name",
    [
        ("Иванов Иван Иванович", "иванович"),
        ("Иванов Иван", ""),
    ],
)
def test_add_late_catcher_by_full_name_adds_existing_user(
    session,
    user_factory,
    full_name,
    by_father_name,
):
    user = user_factory(by_father_name=by_father_name)

    result = add_late_catcher_by_full_name(full_name)

    late_catcher = session.get(LateCatcher, user.id)

    assert result == LATE_CATCHER_ADDED_RESULT
    assert late_catcher is not None


def test_add_late_catcher_by_full_name_returns_message_if_already_late_catcher(
    session,
    user_factory,
):
    user = user_factory()
    add_late_catcher_to_session(session, user)

    result = add_late_catcher_by_full_name("Иванов Иван Иванович")

    late_catchers_count = session.query(LateCatcher).count()

    assert result == "Этот пользователь уже есть в дежурных по опозданиям"
    assert late_catchers_count == 1


def test_add_late_catcher_by_full_name_returns_message_if_user_not_found(session):
    result = add_late_catcher_by_full_name("Иванов Иван Иванович")

    late_catchers_count = session.query(LateCatcher).count()

    assert result == "Пользователь с таким ФИО не найден"
    assert late_catchers_count == 0


def test_add_late_catcher_by_full_name_returns_message_if_full_name_has_wrong_format(
    session,
):
    result = add_late_catcher_by_full_name("Иванов")

    late_catchers_count = session.query(LateCatcher).count()

    assert result == "Введите ФИО в формате: Иванов Иван Иванович или Иванов Иван"
    assert late_catchers_count == 0


def test_get_late_catchers_list_returns_empty_message(session):
    result = get_late_catchers_list()

    assert result == "Список дежурных по опозданиям пуст"


def test_get_user_messenger_ids_by_full_name_returns_both_messenger_ids(user_factory):
    user_factory(vk_id=67890)

    result = get_user_messenger_ids_by_full_name("Иванов Иван Иванович")

    assert result == UserMessengerIds(chat_id=12345, vk_id=67890)


def test_get_user_messenger_ids_by_full_name_returns_none_if_user_not_found(session):
    result = get_user_messenger_ids_by_full_name("Иванов Иван Иванович")

    assert result is None


@pytest.mark.parametrize(
    "by_father_name, expected_late_catcher_full_name",
    [
        ("иванович", "иванов иван иванович"),
        ("", "иванов иван"),
    ],
)
def test_get_late_catchers_list_returns_only_late_catchers(
    session,
    user_factory,
    by_father_name,
    expected_late_catcher_full_name,
):
    late_catcher_user = user_factory(
        surname="иванов",
        name="иван",
        by_father_name=by_father_name,
        chat_id=1,
    )
    user_factory(
        surname="петров",
        name="петр",
        by_father_name="петрович",
        chat_id=2,
    )

    add_late_catcher_to_session(session, late_catcher_user)

    result = get_late_catchers_list()

    assert result == expected_late_catcher_full_name
    assert "петров петр петрович" not in result


@pytest.mark.parametrize(
    "full_name, by_father_name",
    [
        ("Иванов Иван Иванович", "иванович"),
        ("Иванов Иван", ""),
    ],
)
def test_remove_late_catcher_by_full_name_removes_existing_late_catcher(
    session,
    user_factory,
    full_name,
    by_father_name,
):
    user = user_factory(by_father_name=by_father_name)

    add_late_catcher_to_session(session, user)

    result = remove_late_catcher_by_full_name(full_name)

    deleted_late_catcher = session.get(LateCatcher, user.id)

    assert result == LATE_CATCHER_REMOVED_RESULT
    assert deleted_late_catcher is None


def test_remove_late_catcher_by_full_name_returns_message_if_user_is_not_late_catcher(
    session,
    user_factory,
):
    user_factory()

    result = remove_late_catcher_by_full_name("Иванов Иван Иванович")

    late_catchers_count = session.query(LateCatcher).count()

    assert result == "Этого пользователя нет в дежурных по опозданиям"
    assert late_catchers_count == 0


def create_users_with_same_name_and_different_by_father_name(user_factory):
    user_without_by_father_name = user_factory(
        by_father_name="",
        chat_id=1,
    )
    user_with_by_father_name = user_factory(
        by_father_name="иванович",
        chat_id=2,
    )

    return user_without_by_father_name, user_with_by_father_name


def test_add_late_catcher_by_full_name_distinguishes_users_with_and_without_by_father_name(
    session,
    user_factory,
):
    (
        user_without_by_father_name,
        user_with_by_father_name,
    ) = create_users_with_same_name_and_different_by_father_name(user_factory)

    result = add_late_catcher_by_full_name("Иванов Иван")

    late_catcher_without_by_father_name = session.get(
        LateCatcher,
        user_without_by_father_name.id,
    )
    late_catcher_with_by_father_name = session.get(
        LateCatcher,
        user_with_by_father_name.id,
    )

    assert result == LATE_CATCHER_ADDED_RESULT
    assert late_catcher_without_by_father_name is not None
    assert late_catcher_with_by_father_name is None


def test_remove_late_catcher_by_full_name_distinguishes_users_with_and_without_by_father_name(
    session,
    user_factory,
):
    (
        user_without_by_father_name,
        user_with_by_father_name,
    ) = create_users_with_same_name_and_different_by_father_name(user_factory)

    add_late_catcher_to_session(session, user_without_by_father_name)
    add_late_catcher_to_session(session, user_with_by_father_name)

    result = remove_late_catcher_by_full_name("Иванов Иван")

    deleted_late_catcher_without_by_father_name = session.get(
        LateCatcher,
        user_without_by_father_name.id,
    )
    remaining_late_catcher_with_by_father_name = session.get(
        LateCatcher,
        user_with_by_father_name.id,
    )

    assert result == LATE_CATCHER_REMOVED_RESULT
    assert deleted_late_catcher_without_by_father_name is None
    assert remaining_late_catcher_with_by_father_name is not None


@pytest.mark.parametrize(
    "full_name",
    [
        "Иванов Иван Иванович",
        "Иванов Иван",
    ],
)
def test_remove_late_catcher_by_full_name_returns_message_if_user_not_found(
    session,
    full_name,
):
    result = remove_late_catcher_by_full_name(full_name)

    late_catchers_count = session.query(LateCatcher).count()

    assert result == "Пользователь с таким ФИО не найден"
    assert late_catchers_count == 0


def test_remove_late_catcher_by_full_name_returns_message_if_full_name_has_wrong_format(
    session,
):
    result = remove_late_catcher_by_full_name("Иванов")

    late_catchers_count = session.query(LateCatcher).count()

    assert result == "Введите ФИО в формате: Иванов Иван Иванович или Иванов Иван"
    assert late_catchers_count == 0


@pytest.mark.parametrize(
    "messenger_id, messenger_id_tag, expected_found",
    [
        (12345, User.chat_id, True),
        (67890, User.vk_id, True),
        (999, User.chat_id, False),
    ],
)
def test_get_user_id_by_messenger_id(
    user_factory,
    messenger_id,
    messenger_id_tag,
    expected_found,
):
    user = user_factory(
        chat_id=12345,
        vk_id=67890,
    )

    result = get_user_id_by_messenger_id(
        messenger_id=messenger_id,
        messenger_id_tag=messenger_id_tag,
    )

    if expected_found:
        assert result == user.id
    else:
        assert result is None
