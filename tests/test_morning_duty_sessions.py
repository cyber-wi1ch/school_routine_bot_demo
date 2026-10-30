from datetime import date, datetime

from school_routine_bot.db_files.db_models import MorningDutySession, User
from school_routine_bot.morning_duty_sessions import (
    MorningDutySessionInfo,
    delete_morning_duty_session,
    finish_morning_duty_session,
    get_finished_morning_duty_sessions,
    get_morning_duty_session_info,
    start_morning_duty_session,
)


def create_user(
    session,
    surname="иванов",
    name="иван",
    by_father_name="иванович",
    chat_id=12345,
    vk_id=None,
):
    # noinspection PyArgumentList
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


def test_start_morning_duty_session_creates_session(session):
    user = create_user(session)

    session_id = start_morning_duty_session(
        late_catcher_user_id=user.id,
        late_catcher_full_name="иванов иван иванович",
        duty_date=date(2026, 7, 28),
        building_address="1 корпус",
        started_at=datetime(2026, 7, 28, 8, 0),
    )

    morning_duty_session = session.get(MorningDutySession, session_id)

    assert morning_duty_session is not None
    assert morning_duty_session.late_catcher_user_id == user.id
    assert morning_duty_session.late_catcher_full_name == "иванов иван иванович"
    assert morning_duty_session.duty_date == date(2026, 7, 28)
    assert morning_duty_session.building_address == "1 корпус"
    assert morning_duty_session.started_at == datetime(2026, 7, 28, 8, 0)
    assert morning_duty_session.finished_at is None


def test_start_morning_duty_session_keeps_first_started_at(session):
    user = create_user(session)

    first_session_id = start_morning_duty_session(
        late_catcher_user_id=user.id,
        late_catcher_full_name="иванов иван иванович",
        duty_date=date(2026, 7, 28),
        building_address="1 корпус",
        started_at=datetime(2026, 7, 28, 8, 0),
    )

    second_session_id = start_morning_duty_session(
        late_catcher_user_id=user.id,
        late_catcher_full_name="иванов иван иванович",
        duty_date=date(2026, 7, 28),
        building_address="1 корпус",
        started_at=datetime(2026, 7, 28, 8, 30),
    )

    morning_duty_session = session.get(MorningDutySession, first_session_id)

    assert second_session_id == first_session_id
    assert morning_duty_session.started_at == datetime(2026, 7, 28, 8, 0)


def test_start_morning_duty_session_updates_existing_session(session):
    user = create_user(session)
    duty_date = date(2026, 7, 28)

    session_id = start_morning_duty_session(
        late_catcher_user_id=user.id,
        late_catcher_full_name="иванов иван иванович",
        duty_date=duty_date,
        building_address="1 корпус",
        started_at=datetime(2026, 7, 28, 8, 0),
    )

    finish_morning_duty_session(
        late_catcher_user_id=user.id,
        duty_date=duty_date,
        finished_at=datetime(2026, 7, 28, 9, 0),
    )

    start_morning_duty_session(
        late_catcher_user_id=user.id,
        late_catcher_full_name="иванов иван иванович",
        duty_date=duty_date,
        building_address="2 корпус",
        started_at=datetime(2026, 7, 28, 8, 30),
    )

    morning_duty_session = session.get(MorningDutySession, session_id)

    assert morning_duty_session.building_address == "2 корпус"
    assert morning_duty_session.started_at == datetime(2026, 7, 28, 8, 0)
    assert morning_duty_session.finished_at is None


def test_finish_morning_duty_session_sets_finished_at(session):
    user = create_user(session)
    duty_date = date(2026, 7, 28)

    session_id = start_morning_duty_session(
        late_catcher_user_id=user.id,
        late_catcher_full_name="иванов иван иванович",
        duty_date=duty_date,
        building_address="1 корпус",
        started_at=datetime(2026, 7, 28, 8, 0),
    )

    finished_session_id = finish_morning_duty_session(
        late_catcher_user_id=user.id,
        duty_date=duty_date,
        finished_at=datetime(2026, 7, 28, 9, 0),
    )

    morning_duty_session = session.get(MorningDutySession, session_id)

    assert finished_session_id == session_id
    assert morning_duty_session.finished_at == datetime(2026, 7, 28, 9, 0)


def test_finish_morning_duty_session_updates_finished_at(session):
    user = create_user(session)
    duty_date = date(2026, 7, 28)

    session_id = start_morning_duty_session(
        late_catcher_user_id=user.id,
        late_catcher_full_name="иванов иван иванович",
        duty_date=duty_date,
        building_address="1 корпус",
        started_at=datetime(2026, 7, 28, 8, 0),
    )

    finish_morning_duty_session(
        late_catcher_user_id=user.id,
        duty_date=duty_date,
        finished_at=datetime(2026, 7, 28, 9, 0),
    )
    finish_morning_duty_session(
        late_catcher_user_id=user.id,
        duty_date=duty_date,
        finished_at=datetime(2026, 7, 28, 9, 30),
    )

    morning_duty_session = session.get(MorningDutySession, session_id)

    assert morning_duty_session.finished_at == datetime(2026, 7, 28, 9, 30)


def test_finish_morning_duty_session_returns_none_without_session(session):
    user = create_user(session)

    result = finish_morning_duty_session(
        late_catcher_user_id=user.id,
        duty_date=date(2026, 7, 28),
        finished_at=datetime(2026, 7, 28, 9, 0),
    )

    assert result is None


def test_get_morning_duty_session_info_returns_session_info(session):
    user = create_user(session)
    duty_date = date(2026, 7, 28)
    started_at = datetime(2026, 7, 28, 8, 0)

    session_id = start_morning_duty_session(
        late_catcher_user_id=user.id,
        late_catcher_full_name="иванов иван иванович",
        duty_date=duty_date,
        building_address="1 корпус",
        started_at=started_at,
    )

    result = get_morning_duty_session_info(
        late_catcher_user_id=user.id,
        duty_date=duty_date,
    )

    assert result == MorningDutySessionInfo(
        id=session_id,
        late_catcher_user_id=user.id,
        late_catcher_full_name="иванов иван иванович",
        duty_date=duty_date,
        building_address="1 корпус",
        started_at=started_at,
        finished_at=None,
    )


def test_get_morning_duty_session_info_returns_none_without_session(session):
    user = create_user(session)

    result = get_morning_duty_session_info(
        late_catcher_user_id=user.id,
        duty_date=date(2026, 7, 28),
    )

    assert result is None


def test_delete_morning_duty_session_deletes_session(session):
    user = create_user(session)
    session_id = start_morning_duty_session(
        late_catcher_user_id=user.id,
        late_catcher_full_name="иванов иван иванович",
        duty_date=date(2026, 7, 28),
        building_address="1 корпус",
        started_at=datetime(2026, 7, 28, 8, 0),
    )

    delete_morning_duty_session(session_id)

    morning_duty_session = session.get(MorningDutySession, session_id)

    assert morning_duty_session is None


def test_delete_morning_duty_session_does_not_fail_without_session(session):
    delete_morning_duty_session(999)

    assert session.get(MorningDutySession, 999) is None


def test_get_finished_morning_duty_sessions_returns_empty_list_without_sessions(
    session,
):
    assert get_finished_morning_duty_sessions() == []


def create_finished_morning_duty_session(
    user,
    duty_date: date,
    building_address: str,
    started_at: datetime,
    finished_at: datetime,
) -> int:
    session_id = start_morning_duty_session(
        late_catcher_user_id=user.id,
        late_catcher_full_name=f"{user.surname} {user.name} {user.by_father_name}",
        duty_date=duty_date,
        building_address=building_address,
        started_at=started_at,
    )
    finish_morning_duty_session(
        late_catcher_user_id=user.id,
        duty_date=duty_date,
        finished_at=finished_at,
    )
    return session_id


def test_get_finished_morning_duty_sessions_returns_only_finished_sessions(session):
    first_user = create_user(session)
    second_user = create_user(
        session,
        surname="петров",
        name="петр",
        by_father_name="петрович",
        chat_id=67890,
    )

    unfinished_session_id = start_morning_duty_session(
        late_catcher_user_id=first_user.id,
        late_catcher_full_name="иванов иван иванович",
        duty_date=date(2026, 7, 28),
        building_address="1 корпус",
        started_at=datetime(2026, 7, 28, 8, 0),
    )

    first_finished_session_id = create_finished_morning_duty_session(
        first_user,
        duty_date=date(2026, 7, 29),
        building_address="2 корпус",
        started_at=datetime(2026, 7, 29, 8, 0),
        finished_at=datetime(2026, 7, 29, 9, 0),
    )
    second_finished_session_id = create_finished_morning_duty_session(
        second_user,
        duty_date=date(2026, 7, 29),
        building_address="1 корпус",
        started_at=datetime(2026, 7, 29, 8, 10),
        finished_at=datetime(2026, 7, 29, 9, 10),
    )

    result = get_finished_morning_duty_sessions()

    assert result == [
        MorningDutySessionInfo(
            id=first_finished_session_id,
            late_catcher_user_id=first_user.id,
            late_catcher_full_name="иванов иван иванович",
            duty_date=date(2026, 7, 29),
            building_address="2 корпус",
            started_at=datetime(2026, 7, 29, 8, 0),
            finished_at=datetime(2026, 7, 29, 9, 0),
        ),
        MorningDutySessionInfo(
            id=second_finished_session_id,
            late_catcher_user_id=second_user.id,
            late_catcher_full_name="петров петр петрович",
            duty_date=date(2026, 7, 29),
            building_address="1 корпус",
            started_at=datetime(2026, 7, 29, 8, 10),
            finished_at=datetime(2026, 7, 29, 9, 10),
        ),
    ]
    assert unfinished_session_id not in [
        morning_duty_session.id for morning_duty_session in result
    ]
