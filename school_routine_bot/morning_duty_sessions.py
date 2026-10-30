from dataclasses import dataclass
from datetime import date, datetime

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from school_routine_bot.db_files.db_create import get_session
from school_routine_bot.db_files.db_models import MorningDutySession


@dataclass(frozen=True)
class MorningDutySessionInfo:
    id: int
    late_catcher_user_id: int
    late_catcher_full_name: str
    duty_date: date
    building_address: str
    started_at: datetime
    finished_at: datetime | None


def _get_morning_duty_session(
    session,
    late_catcher_user_id: int,
    duty_date: date,
) -> MorningDutySession | None:
    return (
        session.query(MorningDutySession)
        .filter(
            MorningDutySession.late_catcher_user_id == late_catcher_user_id,
            MorningDutySession.duty_date == duty_date,
        )
        .one_or_none()
    )


def get_morning_duty_session_info(
    late_catcher_user_id: int,
    duty_date: date,
) -> MorningDutySessionInfo | None:
    with get_session() as session:
        morning_duty_session = _get_morning_duty_session(
            session,
            late_catcher_user_id,
            duty_date,
        )

        if morning_duty_session is None:
            return None

        return MorningDutySessionInfo(
            id=morning_duty_session.id,
            late_catcher_user_id=morning_duty_session.late_catcher_user_id,
            late_catcher_full_name=morning_duty_session.late_catcher_full_name,
            duty_date=morning_duty_session.duty_date,
            building_address=morning_duty_session.building_address,
            started_at=morning_duty_session.started_at,
            finished_at=morning_duty_session.finished_at,
        )


def start_morning_duty_session(
    late_catcher_user_id: int,
    late_catcher_full_name: str,
    duty_date: date,
    building_address: str,
    started_at: datetime,
) -> int:
    with get_session() as session:
        existing_session = _get_morning_duty_session(
            session,
            late_catcher_user_id,
            duty_date,
        )

        if existing_session:
            existing_session.building_address = building_address
            existing_session.finished_at = None
            session.commit()
            return existing_session.id

        # noinspection PyArgumentList
        morning_duty_session = MorningDutySession(
            late_catcher_user_id=late_catcher_user_id,
            late_catcher_full_name=late_catcher_full_name,
            duty_date=duty_date,
            building_address=building_address,
            started_at=started_at,
            finished_at=None,
        )

        session.add(morning_duty_session)
        session.commit()

        logger.info("Morning duty session started: {}", morning_duty_session.id)
        return morning_duty_session.id


def finish_morning_duty_session(
    late_catcher_user_id: int,
    duty_date: date,
    finished_at: datetime,
) -> int | None:
    with get_session() as session:
        morning_duty_session = _get_morning_duty_session(
            session,
            late_catcher_user_id,
            duty_date,
        )

        if morning_duty_session is None:
            return None

        morning_duty_session.finished_at = finished_at
        session.commit()

        return morning_duty_session.id


def delete_morning_duty_session(session_id: int) -> None:
    with get_session() as session:
        try:
            morning_duty_session = session.get(MorningDutySession, session_id)

            if morning_duty_session is None:
                return

            session.delete(morning_duty_session)
            session.commit()

        except SQLAlchemyError:
            session.rollback()
            logger.exception(
                "Failed to delete morning duty session: {}",
                session_id,
            )


def get_finished_morning_duty_sessions() -> list[MorningDutySessionInfo]:
    with get_session() as session:
        morning_duty_sessions = (
            session.query(MorningDutySession)
            .filter(MorningDutySession.finished_at.isnot(None))
            .order_by(MorningDutySession.id)
            .all()
        )

        return [
            MorningDutySessionInfo(
                id=morning_duty_session.id,
                late_catcher_user_id=morning_duty_session.late_catcher_user_id,
                late_catcher_full_name=morning_duty_session.late_catcher_full_name,
                duty_date=morning_duty_session.duty_date,
                building_address=morning_duty_session.building_address,
                started_at=morning_duty_session.started_at,
                finished_at=morning_duty_session.finished_at,
            )
            for morning_duty_session in morning_duty_sessions
        ]
