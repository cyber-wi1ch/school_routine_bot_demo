from datetime import date, datetime, time

import pytest

import school_routine_bot.google_sheets_morning_duty as morning_duty_sheets
from school_routine_bot.google_sheets_morning_duty import (
    convert_student_rows_to_pydantic_schemes,
    find_students_by_surname,
)
from school_routine_bot.morning_duty_sessions import MorningDutySessionInfo
from school_routine_bot.pending_late_records import PendingLateStudentRecordInfo
from school_routine_bot.pydantic_schemes import StudentFromSheet


def make_pending_late_student_record_info(
    record_id: int = 1,
    late_student_full_name: str = "Александрова Александра Александровна",
) -> PendingLateStudentRecordInfo:
    return PendingLateStudentRecordInfo(
        id=record_id,
        late_catcher_user_id=123,
        late_catcher_full_name="Иванов Иван Иванович",
        building_address="1 корпус",
        late_student_full_name=late_student_full_name,
        grade="7",
        letter="А",
        late_date=date(2026, 7, 31),
        late_time=time(8, 15),
        reason="проспал",
    )


def get_worksheet(mocker, fake_worksheet):
    return mocker.patch.object(
        morning_duty_sheets,
        "get_morning_duty_worksheet",
        return_value=fake_worksheet,
    )


def test_format_sheet_date():
    assert morning_duty_sheets.format_sheet_date(date(2026, 7, 31)) == "31.07.2026"


@pytest.mark.parametrize(
    "value",
    [
        time(8, 15),
        datetime(2026, 7, 31, 8, 15),
    ],
)
def test_format_sheet_time(value):
    assert morning_duty_sheets.format_sheet_time(value) == "08:15"


@pytest.mark.parametrize(
    "rows, expected_students",
    [
        (
            [
                ["ФИО", "КЛАСС", "БУКВА"],
                ["Александрова Александра Александровна", "7", "А"],
                ["Ольха Фаина", "8", "В"],
            ],
            [
                StudentFromSheet(
                    full_name="Александрова Александра Александровна",
                    grade="7",
                    letter="А",
                ),
                StudentFromSheet(
                    full_name="Ольха Фаина",
                    grade="8",
                    letter="В",
                ),
            ],
        ),
        (
            [
                ["ФИО", "КЛАСС", "БУКВА"],
                [],
                ["Только ФИО"],
                ["", "7", "А"],
                ["   ", "7", "А"],
                ["Фамилия Имя", "7"],
                ["Александрова Александра Александровна", "7", "А"],
            ],
            [
                StudentFromSheet(
                    full_name="Александрова Александра Александровна",
                    grade="7",
                    letter="А",
                ),
            ],
        ),
        (
            [
                ["ФИО", "КЛАСС", "БУКВА"],
                ["  Александрова Александра Александровна  ", " 7 ", " А "],
            ],
            [
                StudentFromSheet(
                    full_name="Александрова Александра Александровна",
                    grade="7",
                    letter="А",
                ),
            ],
        ),
    ],
)
def test_convert_student_rows_to_pydantic_schemes_returns_students(
    rows,
    expected_students,
):
    result = convert_student_rows_to_pydantic_schemes(rows)

    assert result == expected_students


@pytest.mark.parametrize(
    "surname, expected_students",
    [
        (
            "александрова",
            [
                StudentFromSheet(
                    full_name="Александрова Александра Александровна",
                    grade="7",
                    letter="А",
                ),
                StudentFromSheet(
                    full_name="Александрова Александрина Александровна",
                    grade="9",
                    letter="Б",
                ),
            ],
        ),
        (
            "АЛЕКСАНДРОВА",
            [
                StudentFromSheet(
                    full_name="Александрова Александра Александровна",
                    grade="7",
                    letter="А",
                ),
                StudentFromSheet(
                    full_name="Александрова Александрина Александровна",
                    grade="9",
                    letter="Б",
                ),
            ],
        ),
        (
            "  Александрова  ",
            [
                StudentFromSheet(
                    full_name="Александрова Александра Александровна",
                    grade="7",
                    letter="А",
                ),
                StudentFromSheet(
                    full_name="Александрова Александрина Александровна",
                    grade="9",
                    letter="Б",
                ),
            ],
        ),
        (
            "мамин-сибиряк",
            [
                StudentFromSheet(
                    full_name="Мамин-Сибиряк Дмитрий Наркисович",
                    grade="10",
                    letter="В",
                ),
            ],
        ),
        (
            "иванов",
            [
                StudentFromSheet(
                    full_name="Иванов Иван Иванович",
                    grade="7",
                    letter="А",
                ),
                StudentFromSheet(
                    full_name="Иванов Иван Иванович",
                    grade="9",
                    letter="Б",
                ),
            ],
        ),
        ("несуществующий", []),
        ("", []),
        ("   ", []),
    ],
)
def test_find_students_by_surname_returns_matching_students(
    surname,
    expected_students,
):
    students = [
        StudentFromSheet(
            full_name="Александрова Александра Александровна",
            grade="7",
            letter="А",
        ),
        StudentFromSheet(
            full_name="Александрова Александрина Александровна",
            grade="9",
            letter="Б",
        ),
        StudentFromSheet(
            full_name="Мамин-Сибиряк Дмитрий Наркисович",
            grade="10",
            letter="В",
        ),
        StudentFromSheet(
            full_name="Иванов Иван Иванович",
            grade="7",
            letter="А",
        ),
        StudentFromSheet(
            full_name="Иванов Иван Иванович",
            grade="9",
            letter="Б",
        ),
    ]

    result = find_students_by_surname(students, surname)

    assert result == expected_students


async def test_get_students_uses_cache(mocker):
    fake_worksheet = mocker.Mock()
    fake_worksheet.get_all_values.return_value = [
        ["ФИО", "КЛАСС", "БУКВА"],
        ["Александрова Александра Александровна", "7", "А"],
    ]

    mocker.patch.object(
        morning_duty_sheets,
        "get_students_worksheet",
        return_value=fake_worksheet,
    )

    await morning_duty_sheets.clear_students_cache()

    morning_duty_sheets.get_students()
    morning_duty_sheets.get_students()

    assert fake_worksheet.get_all_values.call_count == 1


def test_build_late_student_row():
    record = make_pending_late_student_record_info()

    result = morning_duty_sheets.build_late_student_row(record)

    assert result == [
        "Иванов Иван Иванович",
        "Александрова Александра Александровна",
        "7",
        "А",
        "31.07.2026",
        "08:15",
        "1 корпус",
        "проспал",
    ]


def test_build_morning_duty_row():
    duty_record = MorningDutySessionInfo(
        id=1,
        late_catcher_user_id=123,
        late_catcher_full_name="Иванов Иван Иванович",
        building_address="1 корпус",
        duty_date=date(2026, 7, 31),
        started_at=datetime(2026, 7, 31, 9, 15),
        finished_at=datetime(2026, 7, 31, 10, 15),
    )

    result = morning_duty_sheets.build_morning_duty_row(duty_record)

    assert result == [
        "31.07.2026",
        "1 корпус",
        "09:15",
        "10:15",
        "Иванов Иван Иванович",
    ]


def test_build_morning_duty_row_raises_error_without_finished_at():
    duty_record = MorningDutySessionInfo(
        id=1,
        late_catcher_user_id=123,
        late_catcher_full_name="Иванов Иван Иванович",
        building_address="1 корпус",
        duty_date=date(2026, 7, 31),
        started_at=datetime(2026, 7, 31, 9, 15),
        finished_at=None,
    )

    with pytest.raises(ValueError, match="cannot be written without finish time"):
        morning_duty_sheets.build_morning_duty_row(duty_record)


def test_append_late_student_record_to_sheet_appends_record_row(mocker):
    record = make_pending_late_student_record_info()
    fake_worksheet = mocker.Mock()

    gotten_worksheet = get_worksheet(mocker, fake_worksheet)

    morning_duty_sheets.append_late_student_record_to_sheet(record)

    gotten_worksheet.assert_called_once_with(
        morning_duty_sheets.LATE_STUDENTS_WORKSHEET
    )
    fake_worksheet.append_row.assert_called_once_with(
        [
            "Иванов Иван Иванович",
            "Александрова Александра Александровна",
            "7",
            "А",
            "31.07.2026",
            "08:15",
            "1 корпус",
            "проспал",
        ]
    )


def test_append_morning_duty_session_to_sheet(mocker):
    duty_record = MorningDutySessionInfo(
        id=1,
        late_catcher_user_id=123,
        late_catcher_full_name="Иванов Иван Иванович",
        building_address="1 корпус",
        duty_date=date(2026, 7, 31),
        started_at=datetime(2026, 7, 31, 9, 15),
        finished_at=datetime(2026, 7, 31, 10, 15),
    )
    fake_worksheet = mocker.Mock()

    gotten_worksheet = get_worksheet(mocker, fake_worksheet)

    morning_duty_sheets.append_morning_duty_session_to_sheet(duty_record)

    gotten_worksheet.assert_called_once_with(
        morning_duty_sheets.MORNING_DUTIES_WORKSHEET
    )
    fake_worksheet.append_row.assert_called_once_with(
        [
            "31.07.2026",
            "1 корпус",
            "09:15",
            "10:15",
            "Иванов Иван Иванович",
        ]
    )


@pytest.mark.parametrize(
    "append_side_effect, expected_deleted_ids",
    [
        (None, [1, 2]),
        (Exception("Google Sheets failed"), []),
        ([Exception("Google Sheets failed"), None], [2]),
    ],
)
async def test_retry_pending_late_student_records(
    mocker,
    append_side_effect,
    expected_deleted_ids,
):
    records = [
        make_pending_late_student_record_info(record_id=1),
        make_pending_late_student_record_info(
            record_id=2,
            late_student_full_name="Петров Петр Петрович",
        ),
    ]

    mocker.patch.object(
        morning_duty_sheets,
        "get_pending_late_student_records",
        return_value=records,
    )
    append_record = mocker.patch.object(
        morning_duty_sheets,
        "append_late_student_record_to_sheet",
        side_effect=append_side_effect,
    )
    delete_record = mocker.patch.object(
        morning_duty_sheets,
        "delete_pending_late_student_record",
    )

    await morning_duty_sheets.retry_pending_late_student_records()

    assert append_record.call_count == len(records)
    assert [
        call.args[0] for call in delete_record.call_args_list
    ] == expected_deleted_ids


def make_morning_duty_session_info(
    session_id: int = 1,
    late_catcher_full_name: str = "Иванов Иван Иванович",
) -> MorningDutySessionInfo:
    return MorningDutySessionInfo(
        id=session_id,
        late_catcher_user_id=123,
        late_catcher_full_name=late_catcher_full_name,
        duty_date=date(2026, 7, 31),
        building_address="1 корпус",
        started_at=datetime(2026, 7, 31, 9, 15),
        finished_at=datetime(2026, 7, 31, 10, 15),
    )


@pytest.mark.parametrize(
    "append_side_effect, expected_deleted_ids",
    [
        (None, [1, 2]),
        (Exception("Google Sheets failed"), []),
        ([Exception("Google Sheets failed"), None], [2]),
    ],
)
async def test_export_finished_morning_duty_sessions(
    mocker,
    append_side_effect,
    expected_deleted_ids,
):
    records = [
        make_morning_duty_session_info(session_id=1),
        make_morning_duty_session_info(
            session_id=2,
            late_catcher_full_name="Петров Петр Петрович",
        ),
    ]

    mocker.patch.object(
        morning_duty_sheets,
        "get_finished_morning_duty_sessions",
        return_value=records,
    )
    append_record = mocker.patch.object(
        morning_duty_sheets,
        "append_morning_duty_session_to_sheet",
        side_effect=append_side_effect,
    )
    delete_record = mocker.patch.object(
        morning_duty_sheets,
        "delete_morning_duty_session",
    )

    await morning_duty_sheets.export_finished_morning_duty_sessions()

    assert append_record.call_count == len(records)
    assert [
        call.args[0] for call in delete_record.call_args_list
    ] == expected_deleted_ids


async def test_save_late_student_record_creates_pending_record_and_retries(mocker):
    morning_duty_session = MorningDutySessionInfo(
        id=1,
        late_catcher_user_id=123,
        late_catcher_full_name="Иванов Иван Иванович",
        duty_date=date(2026, 8, 11),
        building_address="1 корпус",
        started_at=datetime(2026, 8, 11, 8, 0),
        finished_at=None,
    )

    create_record = mocker.patch.object(
        morning_duty_sheets,
        "create_pending_late_student_record",
    )
    retry_records = mocker.patch.object(
        morning_duty_sheets,
        "retry_pending_late_student_records",
    )

    await morning_duty_sheets.save_late_student_record(
        morning_duty_session=morning_duty_session,
        late_student_full_name="Александрова Александра Александровна",
        grade="7",
        letter="А",
        late_date=date(2026, 8, 11),
        late_time=time(8, 15),
        reason="проспал",
    )

    create_record.assert_called_once_with(
        late_catcher_user_id=123,
        late_catcher_full_name="Иванов Иван Иванович",
        building_address="1 корпус",
        late_student_full_name="Александрова Александра Александровна",
        grade="7",
        letter="А",
        late_date=date(2026, 8, 11),
        late_time=time(8, 15),
        reason="проспал",
    )
    retry_records.assert_awaited_once_with()
