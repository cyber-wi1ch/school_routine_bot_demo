from collections.abc import Sequence
from datetime import date, datetime, time
from functools import cache

from gspread import Worksheet
from loguru import logger

from school_routine_bot.google_sheets_polling import connect
from school_routine_bot.morning_duty_sessions import (
    MorningDutySessionInfo,
    delete_morning_duty_session,
    get_finished_morning_duty_sessions,
)
from school_routine_bot.pending_late_records import (
    PendingLateStudentRecordInfo,
    create_pending_late_student_record,
    delete_pending_late_student_record,
    get_pending_late_student_records,
)
from school_routine_bot.pydantic_schemes import StudentFromSheet
from school_routine_bot.settings import get_settings

STUDENTS_WORKSHEET = "Ученики"
LATE_STUDENTS_WORKSHEET = "Опоздавшие"
MORNING_DUTIES_WORKSHEET = "Утренние дежурства"


def format_sheet_date(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def format_sheet_time(value: time | datetime) -> str:
    return value.strftime("%H:%M")


def get_morning_duty_worksheet(worksheet_title: str) -> Worksheet:
    settings = get_settings()
    _, worksheet = connect(
        settings.credentials_for_tables_file,
        settings.morning_duty_table_url,
        worksheet_title,
    )
    return worksheet


def get_students_worksheet() -> Worksheet:
    return get_morning_duty_worksheet(STUDENTS_WORKSHEET)


def convert_student_rows_to_pydantic_schemes(
    rows: list[list[str]],
) -> list[StudentFromSheet]:
    return [
        StudentFromSheet(
            full_name=row[0].strip(),
            grade=row[1].strip(),
            letter=row[2].strip(),
        )
        for row in rows[1:]
        if len(row) >= 3 and row[0].strip()
    ]


@cache
def get_students() -> tuple[StudentFromSheet, ...]:
    student_worksheet = get_students_worksheet()
    rows = student_worksheet.get_all_values()
    logger.info("Loaded {} rows from students worksheet", len(rows))
    return tuple(convert_student_rows_to_pydantic_schemes(rows))


def find_students_by_surname(
    students: Sequence[StudentFromSheet],
    surname: str,
) -> list[StudentFromSheet]:
    normalized_surname = surname.strip().lower()
    if not normalized_surname:
        return []

    return [
        student
        for student in students
        if student.full_name.lower().startswith(normalized_surname)
    ]


async def clear_students_cache() -> None:
    get_students.cache_clear()


def build_late_student_row(record: PendingLateStudentRecordInfo) -> list[str]:
    return [
        record.late_catcher_full_name,
        record.late_student_full_name,
        record.grade,
        record.letter,
        format_sheet_date(record.late_date),
        format_sheet_time(record.late_time),
        record.building_address,
        record.reason,
    ]


def build_morning_duty_row(record: MorningDutySessionInfo) -> list[str]:
    if record.finished_at is None:
        raise ValueError("Morning duty session cannot be written without finish time")
    return [
        format_sheet_date(record.duty_date),
        record.building_address,
        format_sheet_time(record.started_at),
        format_sheet_time(record.finished_at),
        record.late_catcher_full_name,
    ]


def append_late_student_record_to_sheet(record: PendingLateStudentRecordInfo) -> None:
    worksheet = get_morning_duty_worksheet(LATE_STUDENTS_WORKSHEET)
    worksheet.append_row(build_late_student_row(record))


def append_morning_duty_session_to_sheet(record: MorningDutySessionInfo) -> None:
    worksheet = get_morning_duty_worksheet(MORNING_DUTIES_WORKSHEET)
    worksheet.append_row(build_morning_duty_row(record))


async def retry_pending_late_student_records() -> None:
    records = get_pending_late_student_records()

    for record in records:
        try:
            append_late_student_record_to_sheet(record)
        except Exception:
            logger.exception("Failed to append pending late student record")
            continue
        delete_pending_late_student_record(record.id)


async def save_late_student_record(
    morning_duty_session: MorningDutySessionInfo,
    late_student_full_name: str,
    grade: str,
    letter: str,
    late_date: date,
    late_time: time,
    reason: str,
) -> None:
    create_pending_late_student_record(
        late_catcher_user_id=morning_duty_session.late_catcher_user_id,
        late_catcher_full_name=morning_duty_session.late_catcher_full_name,
        building_address=morning_duty_session.building_address,
        late_student_full_name=late_student_full_name,
        grade=grade,
        letter=letter,
        late_date=late_date,
        late_time=late_time,
        reason=reason,
    )

    await retry_pending_late_student_records()


async def export_finished_morning_duty_sessions() -> None:
    records = get_finished_morning_duty_sessions()

    for record in records:
        try:
            append_morning_duty_session_to_sheet(record)
        except Exception:
            logger.exception("Failed to append morning duty session")
            continue

        delete_morning_duty_session(record.id)


async def retry_morning_duty_exports() -> None:
    await export_finished_morning_duty_sessions()
    await retry_pending_late_student_records()


def add_morning_duty_export_tasks(
    scheduler,
    export_times: list[time],
) -> None:
    for export_time in export_times:
        scheduler.add_daily_task(
            target_time=export_time,
            func=retry_morning_duty_exports,
        )
