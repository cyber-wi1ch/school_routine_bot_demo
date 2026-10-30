from dataclasses import dataclass
from datetime import date, time

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from school_routine_bot.db_files.db_create import get_session
from school_routine_bot.db_files.db_models import PendingLateStudentRecord


@dataclass(frozen=True)
class PendingLateStudentRecordInfo:
    id: int
    late_catcher_user_id: int
    late_catcher_full_name: str
    building_address: str
    late_student_full_name: str
    grade: str
    letter: str
    late_date: date
    late_time: time
    reason: str


def create_pending_late_student_record(
    late_catcher_user_id: int,
    late_catcher_full_name: str,
    building_address: str,
    late_student_full_name: str,
    grade: str,
    letter: str,
    late_date: date,
    late_time: time,
    reason: str,
) -> int:
    with get_session() as session:
        # noinspection PyArgumentList
        late_student_record = PendingLateStudentRecord(
            late_catcher_user_id=late_catcher_user_id,
            late_student_full_name=late_student_full_name,
            late_catcher_full_name=late_catcher_full_name,
            grade=grade,
            letter=letter,
            late_date=late_date,
            late_time=late_time,
            building_address=building_address,
            reason=reason,
        )

        session.add(late_student_record)
        session.commit()

        return late_student_record.id


def get_pending_late_student_records() -> list[PendingLateStudentRecordInfo]:
    with get_session() as session:
        records = (
            session.query(PendingLateStudentRecord)
            .order_by(PendingLateStudentRecord.id)
            .all()
        )

        return [
            PendingLateStudentRecordInfo(
                id=record.id,
                late_catcher_user_id=record.late_catcher_user_id,
                late_catcher_full_name=record.late_catcher_full_name,
                building_address=record.building_address,
                late_student_full_name=record.late_student_full_name,
                grade=record.grade,
                letter=record.letter,
                late_date=record.late_date,
                late_time=record.late_time,
                reason=record.reason,
            )
            for record in records
        ]


def delete_pending_late_student_record(record_id: int) -> None:
    with get_session() as session:
        try:
            record = session.get(PendingLateStudentRecord, record_id)

            if record is None:
                return

            session.delete(record)
            session.commit()

        except SQLAlchemyError:
            session.rollback()
            logger.exception(
                "Failed to delete pending late student record: {}",
                record_id,
            )
