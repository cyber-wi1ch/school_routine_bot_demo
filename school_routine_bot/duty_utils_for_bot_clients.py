from datetime import datetime, time, timedelta

from school_routine_bot.pydantic_schemes import ValidDutyRow
from school_routine_bot.school_scheduler import filter_duties, get_next_datetime


def filter_personal_duty_data_for_now(duty_data: dict[str, list[ValidDutyRow]]) -> dict:
    return filter_duties(
        duty_data,
        datetime.now(),
        get_next_datetime(at=time(17, 00), day_offset=1),
    )


def make_message_for_actual_duties_button(
    duty_date: str, duty_location: str, duty_time: str
) -> str:
    return (
        f"\n🟢 <b>ДАТА</b> - <u>{duty_date}</u>,\n"
        f"<b>МЕСТО</b> - <u>{duty_location}</u>,\n"
        f"<b>ВРЕМЯ</b> - <u>{duty_time}</u>.\n\n"
    )


def make_actual_duty_message_for_person(
    person: str, duty_data: dict[str, list[ValidDutyRow]], chat_id: int
):
    message_1 = ""
    message_2 = ""
    if person in duty_data:
        for duty in duty_data[person]:
            if chat_id == duty.chat_id:
                duty_date = duty.date
                today = datetime.today().date()
                if duty_date > today + timedelta(days=1) or duty_date < today:
                    continue
                if duty_date == today:
                    message_1 += make_message_for_actual_duties_button(
                        duty.date_str, duty.location, duty.time_period_str
                    )
                if today < duty_date < today + timedelta(days=2):
                    message_2 += make_message_for_actual_duties_button(
                        duty.date_str, duty.location, duty.time_period_str
                    )
    return message_1 + message_2


def format_actual_duty_button_text(personal_duty_message: str) -> str:
    return f"⏱️Вы дежурите:\n\n {personal_duty_message}"


# IF ONE MORE SHEET WILL BE NEEDED
# def format_actual_duty_button_text(personal_duty_message: str) -> str:
#     if personal_duty_message.startswith(
#         "<i>(From worksheet 'Duty sign-up')</i>\n "
#         "<i>(From worksheet 'VP duty')</i>\n"
#     ):
#         personal_duty_message = personal_duty_message.replace(
#             "<i>(From worksheet 'Duty sign-up')</i>\n", ""
#         )
#     elif personal_duty_message.startswith(
#         "<i>(From worksheet 'VP duty')</i>\n "
#         "<i>(From worksheet 'Duty sign-up')</i>\n"
#     ):
#         personal_duty_message = personal_duty_message.replace(
#             "<i>(From worksheet 'VP duty')</i>\n", ""
#         )
#
#     personal_duty_message = f"⏱️Your duties:\n\n {personal_duty_message}"
#
#     if personal_duty_message.endswith("VP duty')</i>\n "):
#         personal_duty_message = personal_duty_message.replace(
#             "<i>(From worksheet 'VP duty')</i>\n", ""
#         )
#     elif personal_duty_message.endswith("sign-up')</i>\n "):
#         personal_duty_message = personal_duty_message.replace(
#             "<i>(From worksheet 'Duty sign-up')</i>\n", ""
#         )
#     return personal_duty_message
