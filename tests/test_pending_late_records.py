from datetime import date, time

import pytest

from school_routine_bot.db_files.db_models import PendingLateStudentRecord, User
from school_routine_bot.pending_late_records import (
    PendingLateStudentRecordInfo,
    create_pending_late_student_record,
    delete_pending_late_student_record,
    get_pending_late_student_records,
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


def test_create_pending_late_student_record_creates_record(session):
    user = create_user(session)

    record_id = create_pending_late_student_record(
        late_catcher_user_id=user.id,
        late_catcher_full_name="иванов иван иванович",
        building_address="1 корпус",
        late_student_full_name="петров петр петрович",
        grade="7",
        letter="А",
        late_date=date(2026, 7, 29),
        late_time=time(8, 15),
        reason="проспал",
    )

    pending_record = session.get(PendingLateStudentRecord, record_id)

    assert pending_record is not None
    assert pending_record.late_catcher_user_id == user.id
    assert pending_record.late_catcher_full_name == "иванов иван иванович"
    assert pending_record.building_address == "1 корпус"
    assert pending_record.late_student_full_name == "петров петр петрович"
    assert pending_record.grade == "7"
    assert pending_record.letter == "А"
    assert pending_record.late_date == date(2026, 7, 29)
    assert pending_record.late_time == time(8, 15)
    assert pending_record.reason == "проспал"


def create_pending_record(user, late_student_full_name="петров петр петрович"):
    return create_pending_late_student_record(
        late_catcher_user_id=user.id,
        late_catcher_full_name="иванов иван иванович",
        building_address="1 корпус",
        late_student_full_name=late_student_full_name,
        grade="7",
        letter="А",
        late_date=date(2026, 7, 29),
        late_time=time(8, 15),
        reason="проспал",
    )


@pytest.mark.parametrize(
    "late_student_full_names",
    [
        [],
        ["петров петр петрович"],
        ["петров петр петрович", "сидоров сидор сидорович"],
    ],
)
def test_get_pending_late_student_records_returns_records(
    session,
    late_student_full_names,
):
    user = create_user(session)

    expected_records = []

    for late_student_full_name in late_student_full_names:
        record_id = create_pending_record(
            user,
            late_student_full_name=late_student_full_name,
        )
        expected_records.append(
            PendingLateStudentRecordInfo(
                id=record_id,
                late_catcher_user_id=user.id,
                late_catcher_full_name="иванов иван иванович",
                building_address="1 корпус",
                late_student_full_name=late_student_full_name,
                grade="7",
                letter="А",
                late_date=date(2026, 7, 29),
                late_time=time(8, 15),
                reason="проспал",
            )
        )

    assert get_pending_late_student_records() == expected_records


def test_delete_pending_late_student_record_deletes_record(session):
    user = create_user(session)
    record_id = create_pending_record(user)

    delete_pending_late_student_record(record_id)

    pending_record = session.get(PendingLateStudentRecord, record_id)

    assert pending_record is None
