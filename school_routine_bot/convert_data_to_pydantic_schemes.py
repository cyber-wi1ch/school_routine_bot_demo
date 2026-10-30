from datetime import datetime

from loguru import logger
from pydantic import ValidationError

from school_routine_bot.pydantic_schemes import (
    AvailableDutySlots,
    InvalidDutyRow,
    ValidDutyRow,
)
from school_routine_bot.school_scheduler import (
    cut_time_points_out_of_str,
    define_duration,
)


def convert_data_to_pydantic_schemes(
    duty_data: dict[str, list]
) -> tuple[
    dict[str, list[ValidDutyRow]],
    dict[str, list[AvailableDutySlots]],
    dict[str, list[InvalidDutyRow]],
]:
    valid_duties: dict[str, list[ValidDutyRow]] = {}
    available_duties: dict[str, list[AvailableDutySlots]] = {}
    invalid_duties: dict[str, list[InvalidDutyRow]] = {}
    for person, duties in duty_data.items():
        if person == "":
            for duty in duties:
                try:
                    available_duties[person] = available_duties.get(person, []) + [
                        AvailableDutySlots(**duty)
                    ]
                except (TypeError, ValidationError, KeyError, ValueError) as e:
                    logger.trace(f"Convertion of empty slots failed: {e}")
                    invalid_duties[person] = invalid_duties.get(person, []) + [
                        InvalidDutyRow(
                            date=duty.get("date"),
                            time=duty.get("time"),
                            location=duty.get("location"),
                            duration=duty.get("duration"),
                            chat_id=duty.get("chat_id"),
                            exact_name_from_table=duty.get("exact_name_from_table"),
                            name=duty.get("name"),
                            by_father_name=duty.get("by_father_name"),
                        )
                    ]

        else:
            for duty in duties:
                try:
                    time_1, time_2 = cut_time_points_out_of_str(duty["time"])
                    duration = int(define_duration(time_1, time_2))
                    date = datetime.strptime(duty["date"], "%d.%m.%Y").date()
                    valid_duties[person] = valid_duties.get(person, []) + [
                        ValidDutyRow(
                            date=date,
                            time_1=datetime.strptime(time_1, "%H:%M").time(),
                            time_2=datetime.strptime(time_2, "%H:%M").time(),
                            location=duty["location"],
                            duration=duration,
                            chat_id=int(duty["chat_id"]),
                            exact_name_from_table=duty["exact_name_from_table"],
                            name=duty["name"],
                            by_father_name=duty["by_father_name"],
                        )
                    ]

                except (TypeError, ValidationError, KeyError, ValueError) as e:
                    logger.trace(f"Convertion failed: {e}")
                    invalid_duties[person] = invalid_duties.get(person, []) + [
                        InvalidDutyRow(
                            date=duty.get("date"),
                            time=duty.get("time"),
                            location=duty.get("location"),
                            duration=duty.get("duration"),
                            chat_id=duty.get("chat_id"),
                            exact_name_from_table=duty.get("exact_name_from_table"),
                            name=duty.get("name"),
                            by_father_name=duty.get("by_father_name"),
                        )
                    ]

    return valid_duties, available_duties, invalid_duties
