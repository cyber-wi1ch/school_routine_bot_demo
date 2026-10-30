from datetime import date, time

from pydantic import BaseModel, computed_field


class ValidDutyRow(BaseModel):
    date: date
    time_1: time
    time_2: time
    location: str
    duration: int | None = None
    chat_id: int
    exact_name_from_table: str
    name: str = ""
    by_father_name: str = ""

    @computed_field  # type: ignore
    @property
    def time_period_str(self) -> str:
        return f"{self.time_1.strftime('%H:%M')} - {self.time_2.strftime('%H:%M')}"

    @computed_field  # type: ignore
    @property
    def date_str(self) -> str:
        return f"{self.date.strftime('%d.%m.%Y')}"


class AvailableDutySlots(BaseModel):
    date: str
    location: str
    time: str


class InvalidDutyRow(BaseModel):
    date: str = ""
    time: str = ""
    location: str | None = None
    duration: str | None = None
    chat_id: str | int | None = None
    exact_name_from_table: str | None = None
    name: str | None = None
    by_father_name: str | None = None


class StudentFromSheet(BaseModel):
    full_name: str
    grade: str
    letter: str
