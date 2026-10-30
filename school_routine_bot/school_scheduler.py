import json
from datetime import date, datetime, time, timedelta
from functools import cache
from pathlib import Path
from typing import Callable

from loguru import logger

from school_routine_bot.pydantic_schemes import (
    AvailableDutySlots,
    InvalidDutyRow,
    ValidDutyRow,
)


class CallCounter:
    def __init__(self, func):
        self.func = func
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        logger.info(f"Вызов функции '{self.func.__name__}', раз: {self.calls}")
        return self.func(*args, **kwargs)


def count_calls_class(func):
    return CallCounter(func)


@cache
@count_calls_class
def prepare_to_notify_admins(admin_base: str):
    with open(Path(__file__).parent / admin_base) as f:
        cached_admins = json.load(f)
    admin_dict = {}
    for admin in cached_admins:
        admin_full_name_prefix = (
            f"{upper_first_letter(admin['name'])} "
            f"{upper_first_letter(admin['by_father_name'])}"
        )
        admin_dict.update({admin["admin_id"]: admin_full_name_prefix})
    return admin_dict


def upper_first_letter(name: str) -> str:
    if name:
        return name[0].upper() + name[1::]
    return ""


def handle_the_russian_letter_e_with_dots_in_name(name: str) -> str:
    return name.lower().replace("ё", "е").strip()


def turn_english_alike_letters_into_russian(name: str) -> str:
    alike_letters = {
        "a": "а",
        "A": "а",
        "K": "к",
        "E": "е",
        "e": "е",
        "O": "о",
        "o": "о",
        "p": "р",
        "P": "р",
        "H": "н",
        "X": "х",
        "x": "х",
        "C": "с",
        "c": "с",
        "B": "в",
        "M": "м",
        "T": "т",
        "y": "у",
    }
    for letter in name:
        if letter in alike_letters:
            name = name.replace(letter, alike_letters[letter])
    return handle_the_russian_letter_e_with_dots_in_name(name)


def turn_duty_into_message(duty: ValidDutyRow) -> str:
    message = (
        f"Информация о Вашем дежурстве, {upper_first_letters_in_complex_names(duty.name)} "
        f"{upper_first_letters_in_complex_names(duty.by_father_name)}📝:\n"
        "\n"
        f"📅Дата - <u>{duty.date_str}</u>\n"
        f"⏰Время - <b><u>{duty.time_period_str}</u></b>\n"
        f"🏫Место - <b><u>{duty.location}</u></b>\n"
        f"⏳Длительность - <u>{duty.duration} минут</u>\n"
        "\n"
        "<i>❕Если есть вопросы по дежурству, "
        "обратитесь к ответственному за расписание.</i>"
    )
    return message


def handle_not_standard_time_points(time_point: str) -> str:
    if time_point:
        index = time_point.find(":")
        hours = int(time_point[:index])
        minutes = int(time_point[index + 1 :])
        if len(str(minutes)) <= 2 and hours <= 23:
            if int(time_point[index + 1]) > 5:
                new_hours = str(hours + 1)
                new_minutes = str(minutes - 60)
                if int(new_hours) <= 23:
                    if len(new_minutes) <= 1:
                        return f"{new_hours}:0{new_minutes}"
                    return f"{new_hours}:{new_minutes}"
                else:
                    raise ValueError(
                        "Time input is incorrect. Check the Google table worksheet, please."
                    )
            else:
                return time_point
        else:
            raise ValueError(
                "Time input is incorrect. Check the Google table worksheet, please."
            )
    else:
        return ""


def cut_time_points_out_of_str(time_period: str) -> tuple[str, str]:
    if time_period == "":
        pass
    time_period = time_period.replace(".", ":")
    time_period = time_period.replace("–", "-")
    time_line_1 = ""
    time_line_2 = ""
    index = time_period.find("-")
    if index == -1:
        index = time_period.find("д")
    first_time = ""
    second_time = ""
    if index != -1:
        first_time += time_period[:index]
        second_time += time_period[index:]
    for s in first_time:
        if s.isdigit() or s == ":":
            time_line_1 += s
    for s in second_time:
        if s.isdigit() or s == ":":
            time_line_2 += s
    return handle_not_standard_time_points(
        time_line_1
    ), handle_not_standard_time_points(
        time_line_2
    )  # try to handle it here and above create the handling func


def define_duration(time_line_1: str, time_line_2: str) -> str:
    time_1 = datetime.strptime(time_line_1, "%H:%M")
    time_2 = datetime.strptime(time_line_2, "%H:%M")
    try:
        duration = str(time_2 - time_1).replace(":00", "")
        if duration.isdigit():
            duration += ":00"
        hours, minutes = map(int, duration.split(":"))
        total_minutes = (hours * 60) + minutes
    except ValueError:
        return (
            f"Кажется, временной промежуток нереалистичен,"
            f"проверьте: {time_1} - {time_2}"
        )
    return str(total_minutes)


def make_the_duty_data_info_actual(data: dict) -> dict:
    for person, duties in data.items():
        for duty in duties:
            try:
                if duty.get("user_choice_time"):
                    duty["time"] = duty["user_choice_time"]
                    del duty["user_choice_time"]
                time_1, time_2 = cut_time_points_out_of_str(duty["time"])
                duty["duration"] = define_duration(time_1, time_2)
                duty["time"] = f"{time_1} - {time_2}"
            except ValueError as e:
                logger.error(f"{e} place: {duty['location']} time: {duty['time']}")
    return data


def get_next_datetime(
    at: time, related_to: datetime | None = None, day_offset: int = 0
) -> datetime:
    related_to = related_to or datetime.now()
    target_time = datetime.combine(related_to.date(), time=at) + timedelta(day_offset)
    return target_time if related_to < target_time else target_time + timedelta(days=1)


def get_duty_datetime(duty: ValidDutyRow) -> datetime:
    duty_date = duty.date
    return datetime.combine(duty_date, duty.time_1)


def filter_duties(
    data: dict[str, list[ValidDutyRow]], from_time: datetime, to_time: datetime
) -> dict[str, list[ValidDutyRow]]:
    sorted_duty_info: dict = {}
    if data:
        for person, duties in data.items():
            for duty in duties:
                try:
                    if from_time <= get_duty_datetime(duty) <= to_time:
                        sorted_duty_info[person] = sorted_duty_info.get(person, []) + [
                            duty
                        ]
                except ValueError as e:
                    logger.error(
                        f"{e} place: {duty.location} time: {duty.time_period_str}"
                    )
    return sorted_duty_info


def sort_data_by_certain_time_period(
    data: dict[str, list[ValidDutyRow]], day_offset: int = 1
) -> dict[str, list[ValidDutyRow]]:
    sorted_duty_info: dict[str, list[ValidDutyRow]] = {}
    point_hour = datetime.min.time().replace(hour=17)
    today = datetime.today().date()
    tomorrow = today + timedelta(days=day_offset)
    start_time = datetime.combine(today, point_hour)
    stop_time = datetime.combine(tomorrow, point_hour)
    for person, duties in data.items():
        for duty in duties:
            try:
                duty_date = duty.date
                time_1 = duty.time_1
                # duty_time = datetime.strptime(time_1, "%H:%M").time()
                duty_datetime = datetime.combine(duty_date, time_1)
                if start_time <= duty_datetime <= stop_time:
                    sorted_duty_info[person] = sorted_duty_info.get(person, []) + [duty]
            except ValueError as e:
                logger.error(f"{e} place: {duty.location} time: {duty.time_period_str}")
    return sorted_duty_info


def sort_data_by_certain_time_for_av_duty_slots_and_invalid_data(
    available_duty_slots: dict[str, list[AvailableDutySlots]],
    invalid_data: dict[str, list[InvalidDutyRow]],
    day_offset: int = 1,
) -> tuple[dict, dict]:
    sorted_empty_duty_info: dict[str, list[AvailableDutySlots]] = {}
    sorted_invalid_duty_info: dict[str, list[InvalidDutyRow]] = {}
    point_hour = datetime.min.time().replace(hour=17)
    today = datetime.today().date()
    tomorrow = today + timedelta(days=day_offset)
    start_time = datetime.combine(today, point_hour)
    stop_time = datetime.combine(tomorrow, point_hour)
    for empty_duty in available_duty_slots.get("", []):
        try:
            duty_date = datetime.strptime(empty_duty.date, "%d.%m.%Y").date()
            time_1, time_2 = cut_time_points_out_of_str(empty_duty.time)
            duty_time = datetime.strptime(time_1, "%H:%M").time()
            duty_datetime = datetime.combine(duty_date, duty_time)
            if start_time <= duty_datetime <= stop_time:
                sorted_empty_duty_info[""] = sorted_empty_duty_info.get("", []) + [
                    empty_duty
                ]
        except ValueError as e:
            logger.error(f"{e} place: {empty_duty.location} time: {empty_duty.time}")
    for person, invalid_duties in invalid_data.items():
        for invalid_duty in invalid_duties:
            try:
                duty_date = datetime.strptime(invalid_duty.date, "%d.%m.%Y").date()
                time_1, time_2 = cut_time_points_out_of_str(invalid_duty.time)
                duty_time = datetime.strptime(time_1, "%H:%M").time()
                duty_datetime = datetime.combine(duty_date, duty_time)
                if start_time <= duty_datetime <= stop_time:
                    sorted_invalid_duty_info[person] = sorted_invalid_duty_info.get(
                        person, []
                    ) + [invalid_duty]
            except ValueError as e:
                logger.error(
                    f"{e} place: {invalid_duty.location} time: {invalid_duty.time}"
                )

    return sorted_empty_duty_info, sorted_invalid_duty_info


def get_available_ids_and_not_bot_users(
    valid_data: dict[str, list[ValidDutyRow]],
    invalid_data: dict[str, list[InvalidDutyRow]],
) -> tuple[set, list]:
    available_people_ids = set()
    not_available_people = set()

    for person, duties in valid_data.items():
        for duty in duties:
            available_people_ids.add(duty.chat_id)
    for person, invalid_duties in invalid_data.items():
        for invalid_duty in invalid_duties:
            if not invalid_duty.chat_id:
                if invalid_duty.exact_name_from_table:
                    name_and_father_name = " ".join(
                        [
                            upper_first_letter(s)
                            for s in invalid_duty.exact_name_from_table.split(" ")[1:]
                        ]
                    )
                    not_available_people.add(
                        f"{upper_first_letters_in_complex_names(person)} "
                        f"{name_and_father_name}"
                    )
                else:
                    not_available_people.add(upper_first_letter(person))
    return available_people_ids, list(not_available_people)


def assemble_duty_info_for_each_person(person_id: int, sorted_data) -> list[str]:
    message = []
    for person, duties in sorted_data.items():
        for duty in duties:
            if duty.chat_id == person_id:
                message.append(turn_duty_into_message(duty))
    return message


def is_it_not_saturday():
    return date.today().weekday() not in {5}


def turn_empty_duty_slots_into_message(empty_slots: list[AvailableDutySlots]) -> str:
    message = ""
    date = ""
    for duty in empty_slots:
        date = duty.date
        message += f"<b>{duty.time}</b> <i>{duty.location}</i>\n"
    return f"<b><u>{date}</u></b>\n\n{message}"


def turn_names_into_column(names: list) -> str:
    column = ""
    for s in names:
        column += f"{s}\n"
    return column


def upper_first_letters_in_complex_names(surname: str) -> str:
    return "-".join(upper_first_letter(s) for s in surname.split("-"))


def get_person_id(person: str, data: dict[str, list[ValidDutyRow]]) -> int | None:
    chat_id = None
    if person in data:
        if data[person][0].chat_id:
            chat_id = data[person][0].chat_id
    return chat_id


class SchoolScheduler:
    def __init__(self, notify: Callable):
        self.notify = notify

    async def set_table_data(self, valid_data, available_data, invalid_data):
        pass
