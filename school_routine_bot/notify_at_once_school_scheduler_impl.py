from copy import deepcopy
from datetime import datetime, time
from typing import Callable, cast

from loguru import logger

from school_routine_bot.pydantic_schemes import (
    AvailableDutySlots,
    InvalidDutyRow,
    ValidDutyRow,
)
from school_routine_bot.school_scheduler import (
    SchoolScheduler,
    assemble_duty_info_for_each_person,
    filter_duties,
    get_next_datetime,
    get_person_id,
    prepare_to_notify_admins,
    upper_first_letter,
)


def get_edited_duties(
    removed_duties: list[ValidDutyRow], added_duties: list[ValidDutyRow]
):
    critical_fields = ["date", "chat_id"]
    considered_fields = ["time_period_str", "location"]

    edited_duties = []

    for r_i, removed_duty in enumerate(removed_duties):
        for a_i, added_duty in enumerate(added_duties):
            no_critical_problems = all(
                getattr(removed_duty, f) == getattr(added_duty, f)
                for f in critical_fields
            )
            less_then_2_non_critical_mismatches = [
                getattr(removed_duty, f) == getattr(added_duty, f)
                for f in considered_fields
            ].count(False) < 2
            if no_critical_problems and less_then_2_non_critical_mismatches:
                edited_duties += [((r_i, removed_duty), (a_i, added_duty))]
                break

    return edited_duties


def get_taken_away_duties(duties_old: dict, duties_new: dict) -> dict:
    taken_away_duties: dict = {}
    for person, duties in duties_old.items():
        for duty in duties:
            if duty not in duties_new.get(person, []):
                taken_away_duties[person] = taken_away_duties.get(person, []) + [duty]

    taken_away_duties.pop("", None)
    return taken_away_duties


def get_duties_diff(duties_old: dict, duties_new: dict) -> tuple[dict, dict]:
    taken_away_duties = get_taken_away_duties(duties_old, duties_new)
    added_duties = get_taken_away_duties(duties_new, duties_old)
    return taken_away_duties, added_duties


async def handle_new_people_on_duty(
    admin_base: str,
    old_data: dict,
    new_data: dict,
    added_duties: dict,
    notify,
    notify_about_added: bool,
) -> dict:
    added_duties = deepcopy(added_duties)
    new_people_stats = {}
    for person, new_duties in new_data.items():
        if person not in old_data and person != "":
            if new_duties:
                new_people_stats[person] = new_duties
            del added_duties[person]

    for person in new_people_stats:
        person_id = get_person_id(person, new_people_stats)
        if person_id:
            for message in assemble_duty_info_for_each_person(
                person_id, new_people_stats
            ):
                if notify_about_added:
                    await notify(person_id, message, parse_mode="html")
                logger.info(f"DUTY WAS ADDED {message}")
        else:
            logger.warning(f"Cannot write to unknown user: {person}")
            for admin_id, admin_name in prepare_to_notify_admins(admin_base).items():
                await notify(
                    admin_id,
                    f"{admin_name}, этот человек еще не зарегистрирован в боте - "
                    f" {upper_first_letter(person)}",
                )
    return added_duties


async def handle_no_more_on_duty(
    old_data: dict[str, list[ValidDutyRow]],
    page_title: str,
    new_data: dict[str, list[ValidDutyRow]],
    taken_away_duties: dict,
    notify,
) -> dict:
    taken_away_duties = deepcopy(taken_away_duties)

    removed_people_stats = {}
    for person, removed_duties in old_data.items():
        if person not in new_data and person != "":
            person_id = get_person_id(person, old_data)

            removed_people_stats[person] = removed_duties
            del taken_away_duties[person]
            if removed_duties and person_id:
                if removed_duties[0].date:
                    await notify(
                        person_id,
                        f"У Вас больше нет дежурств на {removed_duties[0].date_str}.🪶"
                        f"\n<i>(В листе таблицы '{page_title}')</i>",
                        parse_mode="html",
                    )
            else:
                pass
    return taken_away_duties


def turn_duty_diff_into_message(was: ValidDutyRow, became: ValidDutyRow) -> str:
    human_readable_fields = {
        "location": "Место",
        "date": "Дата",
        "time_period_str": "Время",
        "duration": "Длительность",
    }

    was_dict = {
        human_readable_fields[k]: v
        for k, v in was.dict().items()
        if k in human_readable_fields
    }
    became_dict = {
        human_readable_fields[k]: v
        for k, v in became.dict().items()
        if k in human_readable_fields
    }

    return "".join(
        [
            "БЫЛО: ",
            "; ".join(
                f"{key}: {val}"
                for key, val in set(was_dict.items()) - set(became_dict.items())
            ),
            "\n",
            "<b><u>СТАЛО</u></b>: ",
            "; ".join(
                f"<b>{key}: {val}</b>"
                for key, val in set(became_dict.items()) - set(was_dict.items())
            ),
        ]
    )


async def handle_edited_duties(
    added_duties: dict,
    taken_away_duties: dict,
    notify,
):
    added_duties = deepcopy(added_duties)
    taken_away_duties = deepcopy(taken_away_duties)
    edited_duties_stats: dict = {}

    for person in set(taken_away_duties) & set(added_duties):
        for (r_i, removed), (a_i, added) in reversed(
            get_edited_duties(taken_away_duties[person], added_duties[person])
        ):
            try:
                del taken_away_duties[person][r_i]
                del added_duties[person][a_i]
            except IndexError as e:
                logger.exception(e)
            edited_duties_stats[person] = edited_duties_stats.get(person, []) + [
                (removed, added)
            ]
        if not taken_away_duties[person]:
            del taken_away_duties[person]
        if not added_duties[person]:
            del added_duties[person]

    for person, duties in edited_duties_stats.items():
        duties = cast(list[tuple[ValidDutyRow, ValidDutyRow]], duties)
        for was, became in duties:
            stats_message_part = turn_duty_diff_into_message(was, became)
            await notify(
                was.chat_id,
                (
                    "Ваше дежурство в месте "
                    f"'{upper_first_letter(was.location)}' "
                    f"в <b>{was.time_period_str}</b> "
                    f"было изменено.\n\n{stats_message_part}"
                ),
                parse_mode="html",
            )

    return added_duties, taken_away_duties


async def handle_add_new_duties(
    added_duties: dict, notify, notify_about_added: bool
) -> dict:
    for person in added_duties:
        if person_id := get_person_id(person, added_duties):
            for message in assemble_duty_info_for_each_person(person_id, added_duties):
                if notify_about_added:
                    await notify(person_id, message, parse_mode="html")
                logger.info(f" {person_id} Добавилось такое дежурство!\n{message}")
    return added_duties


async def handle_delete_some_duties(removed_duties: dict, notify) -> dict:
    for person in removed_duties:
        if person_id := get_person_id(person, removed_duties):
            for message in assemble_duty_info_for_each_person(
                person_id, removed_duties
            ):
                await notify(
                    person_id,
                    f"Кажется, у Вас ОТМЕНИЛОСЬ  это дежурство:\n{message}\n"
                    f"ДАННОЕ ДЕЖУРСТВО БОЛЬШЕ НЕ АКТУАЛЬНО",
                    parse_mode="html",
                )
    return removed_duties


async def notify_people_about_what_have_changed(
    admin_base,
    old_data,
    page_title,
    invalid_data,
    new_data,
    from_time,
    to_time,
    notify,
    notify_about_added: bool,
):
    old_data = filter_duties(old_data, from_time, to_time)
    new_data = filter_duties(new_data, from_time, to_time)

    taken_away_duties, added_duties = get_duties_diff(old_data, new_data)
    logger.debug(
        f"Notify people about what have changed called: {taken_away_duties=} {added_duties=}"
    )

    added_duties__without_new_people = await handle_new_people_on_duty(
        admin_base, old_data, new_data, added_duties, notify, notify_about_added
    )

    taken_away_duties__without_full_disclosure = await handle_no_more_on_duty(
        old_data, page_title, new_data, taken_away_duties, notify
    )

    (
        added_duties__without_editings,
        taken_away_duties__without_editings,
    ) = await handle_edited_duties(
        added_duties__without_new_people,
        taken_away_duties__without_full_disclosure,
        notify,
    )
    await handle_add_new_duties(
        added_duties__without_editings, notify, notify_about_added
    )
    await handle_delete_some_duties(taken_away_duties__without_editings, notify)

    logger.debug(
        f"Sorting stats: {len(taken_away_duties)=} {len(added_duties)=} "
        f"{len(added_duties__without_new_people)=} "
        f"{len(taken_away_duties__without_full_disclosure)=} "
        f"{len(added_duties__without_editings)=} "
        f"{len(taken_away_duties__without_editings)=}"
    )


class NotifyAtOnceSchoolSchedulerImpl(SchoolScheduler):
    def __init__(self, admin_base: str, notify: Callable, page_title: str):
        super().__init__(notify)
        self.data: dict[str, list[ValidDutyRow]] | None = None
        self.admin_base = admin_base
        self.page_title = page_title
        self.invalid_duties: dict[str, list[InvalidDutyRow]] = {}

    async def set_table_data(
        self,
        valid_data: dict[str, list[ValidDutyRow]],
        available_data: dict[str, list[AvailableDutySlots]],
        invalid_data: dict[str, list[InvalidDutyRow]],
    ):
        if self.data is None:
            self.data, self.invalid_duties = valid_data, invalid_data
            return

        await notify_people_about_what_have_changed(
            self.admin_base,
            self.data,
            self.page_title,
            self.invalid_duties,
            valid_data,
            from_time=datetime.now(),
            to_time=get_next_datetime(at=time(17, 00), day_offset=1),
            notify=self.notify,
            notify_about_added=False,
        )

        self.data, self.invalid_duties = valid_data, invalid_data
