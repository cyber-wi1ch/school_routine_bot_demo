from datetime import date, datetime, time

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()
_Base_for_inheritance: type = Base


class User(_Base_for_inheritance):
    __tablename__: str = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    surname: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(30))
    by_father_name: Mapped[str] = mapped_column(String(30))
    chat_id: Mapped[int] = mapped_column(
        BigInteger,  # Data type
        primary_key=False,  # Not a primary key
        unique=True,  # Unique value
        nullable=True,  # MAY BE NULL
        index=True,  # Create an index
        comment="Telegram ID",  # Column comment
        name="telegram_id",  # Database column name (if different from the attribute)
    )
    vk_id: Mapped[int] = mapped_column(
        BigInteger,  # Data type
        primary_key=False,  # Not a primary key
        unique=True,  # Unique value
        nullable=True,  # MAY BE NULL
        index=True,  # Create an index
        comment="VK ID",  # Column comment
        name="vk_id",  # Database column name (if different from the attribute)
    )


class LateCatcher(_Base_for_inheritance):
    __tablename__ = "late_catchers"
    id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)


class Admin(_Base_for_inheritance):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)


class MorningDutySession(_Base_for_inheritance):
    __tablename__ = "morning_duty_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    late_catcher_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    late_catcher_full_name: Mapped[str] = mapped_column(String(100))
    duty_date: Mapped[date] = mapped_column(Date)
    building_address: Mapped[str] = mapped_column(String(150))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PendingLateStudentRecord(_Base_for_inheritance):
    __tablename__ = "pending_late_student_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    late_catcher_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    late_catcher_full_name: Mapped[str] = mapped_column(String(100))
    late_student_full_name: Mapped[str] = mapped_column(String(100))
    grade: Mapped[str] = mapped_column(String(10))
    letter: Mapped[str] = mapped_column(String(10))
    late_date: Mapped[date] = mapped_column(Date)
    late_time: Mapped[time] = mapped_column(Time)
    building_address: Mapped[str] = mapped_column(String(150))
    reason: Mapped[str] = mapped_column(String(500))
