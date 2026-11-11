from typing import Literal

from loguru import logger

from school_routine_bot.db_files.db_create import get_session
from school_routine_bot.db_files.db_models import User
from school_routine_bot.school_scheduler import (
    handle_the_russian_letter_e_with_dots_in_name,
    upper_first_letters_in_complex_names,
)


def normalize_the_input(line: str) -> str:  # makes_the_string_without_spaces_and_tabs
    line = line.replace("\t", "")
    line = "".join(line).replace(" ", "")
    return line.strip()


def cut_the_name_note(name_note: str) -> list:
    return [s for s in name_note.replace(".", " ").split(" ") if s]


def match_initials_with_full_name(
    exact_name_note: str, dict_with_full_name: dict
) -> bool:
    exact_name_note = handle_the_russian_letter_e_with_dots_in_name(exact_name_note)
    name_note_list = cut_the_name_note(exact_name_note)
    if name_note_list[0] == handle_the_russian_letter_e_with_dots_in_name(
        dict_with_full_name["surname"]
    ):
        if len(name_note_list) == 3:
            if handle_the_russian_letter_e_with_dots_in_name(
                dict_with_full_name["name"]
            ).startswith(
                name_note_list[1]
            ) and handle_the_russian_letter_e_with_dots_in_name(
                dict_with_full_name["by_father_name"]
            ).startswith(
                name_note_list[2]
            ):
                return True
            return False
        if len(name_note_list) == 2:
            if handle_the_russian_letter_e_with_dots_in_name(
                dict_with_full_name["name"]
            ).startswith(name_note_list[1]):
                return True
            return False
        else:
            return True
    else:
        return False


def formate_new_user_data(full_name_message: str) -> dict:
    result = {
        "surname": "",
        "name": "",
        "by_father_name": "",
    }
    if full_name_message:
        full_name_message = full_name_message.strip()
        full_name_list = [
            normalize_the_input(s) for s in full_name_message.lower().split()
        ]
        new_user = result
        if len(full_name_list) == 3:
            new_user = {
                "surname": full_name_list[0],
                "name": full_name_list[1],
                "by_father_name": full_name_list[2],
            }
        else:
            if len(full_name_list) == 1:
                new_user = {
                    "surname": full_name_list[0],
                    "name": "",
                    "by_father_name": "",
                }
            elif len(full_name_list) == 2 or len(full_name_list) > 3:
                new_user = {
                    "surname": full_name_list[0],
                    "name": full_name_list[1],
                    "by_father_name": "",
                }

        return new_user
    return result


def get_full_name_from_user_base(user: User) -> dict:
    return {
        "surname": user.surname,
        "name": user.name,
        "by_father_name": user.by_father_name,
    }


class MatcherSchoolBotUsers:
    def __init__(self, messenger_note: Literal["vk", "tg"]):
        self.messenger = messenger_note

        if self.messenger == "vk":
            self.id_tag = User.vk_id
        elif self.messenger == "tg":
            self.id_tag = User.chat_id
        else:
            logger.error("WE HAVE NO ID_TAG")
            return
        logger.info(f"Id-tag {self.id_tag} turned on")

    def write_full_name_into_user_base(self, user_id: int, full_name_message: str):
        with get_session() as session:
            try:
                user = session.query(User).filter(self.id_tag == user_id).one_or_none()
                new_user_dict = formate_new_user_data(full_name_message)

                if not new_user_dict["surname"]:
                    logger.warning(
                        f"Сохранение пользователя {user_id} отклонено: пустое ФИО"
                    )
                    return False

                if user:
                    logger.warning(
                        f"User {user_id} is renaming. "
                        f"was={self.get_user_full_name_by_id(user_id)} "
                        f"became={full_name_message}"
                    )
                    user.surname = new_user_dict["surname"]
                    user.name = new_user_dict["name"]
                    user.by_father_name = new_user_dict["by_father_name"]
                    if self.id_tag == User.chat_id:
                        user.chat_id = user_id
                    elif self.id_tag == User.vk_id:
                        user.vk_id = user_id
                    else:
                        logger.error("WE HAVE NO ID_TAG")
                        return
                    session.commit()

                    logger.info(f"The user {full_name_message} is updated")

                else:
                    old_user = (
                        session.query(User)
                        .filter(
                            User.surname == new_user_dict.get("surname", ""),
                            User.name == new_user_dict.get("name", ""),
                            User.by_father_name
                            == new_user_dict.get("by_father_name", ""),
                        )
                        .first()
                    )
                    if old_user:
                        existing_id = getattr(old_user, self.id_tag.key)
                        if existing_id is not None and existing_id != user_id:
                            logger.warning(
                                f"Регистрация пользователя {user_id} отклонена: "
                                f"у записи {old_user.id} уже другой ID "
                                f"в этом мессенджере"
                            )
                            return False

                        if self.id_tag == User.vk_id:
                            logger.warning(
                                f"User {user_id} {full_name_message} joins vk bot version"
                            )
                            old_user.vk_id = user_id
                        elif self.id_tag == User.chat_id:
                            logger.warning(
                                f"User {user_id} {full_name_message} joins tg bot version"
                            )
                            old_user.chat_id = user_id
                        # Assign the new value
                        session.commit()
                    else:
                        logger.warning(
                            f"User {user_id} is logging as {full_name_message}"
                        )

                        if self.id_tag == User.chat_id:
                            # noinspection PyArgumentList
                            new_user = User(
                                surname=new_user_dict.get("surname", ""),
                                name=new_user_dict.get("name", ""),
                                by_father_name=new_user_dict.get("by_father_name", ""),
                                chat_id=user_id,
                            )

                        elif self.id_tag == User.vk_id:
                            # noinspection PyArgumentList
                            new_user = User(
                                surname=new_user_dict.get("surname", ""),
                                name=new_user_dict.get("name", ""),
                                by_father_name=new_user_dict.get("by_father_name", ""),
                                vk_id=user_id,
                            )

                        else:
                            logger.error("WE HAVE NO ID_TAG")
                            return

                        session.add(new_user)
                        session.commit()
                return True

            except Exception:
                logger.exception(f"Не удалось сохранить данные пользователя {user_id}")
                return False

    def get_user_full_name_by_id(self, user_id: int) -> str:
        with get_session() as session:
            try:
                user = session.query(User).filter(self.id_tag == user_id).one_or_none()
                if user:
                    logger.info(f"Found: {user.surname}")
                    full_name = " ".join(
                        [
                            upper_first_letters_in_complex_names(
                                handle_the_russian_letter_e_with_dots_in_name(
                                    user.surname
                                )
                            ),
                            upper_first_letters_in_complex_names(
                                handle_the_russian_letter_e_with_dots_in_name(user.name)
                            ),
                            upper_first_letters_in_complex_names(
                                handle_the_russian_letter_e_with_dots_in_name(
                                    user.by_father_name
                                )
                            ),
                        ]
                    )
                    return full_name
                else:
                    logger.info("The user is not found")
                    return ""

            except Exception as e:
                logger.exception(
                    f"Found several users with the same chat_id! Exception: {e}"
                )
        return ""

    def add_id_if_match(self, converted_table_data: dict) -> dict:
        with get_session() as session:
            for record in session.query(User).all():
                if person_duties := converted_table_data.get(
                    handle_the_russian_letter_e_with_dots_in_name(record.surname),
                    [],
                ):
                    user = get_full_name_from_user_base(record)
                    for person_duty in person_duties:
                        if "exact_name_from_table" in person_duty:
                            if match_initials_with_full_name(
                                handle_the_russian_letter_e_with_dots_in_name(
                                    person_duty["exact_name_from_table"]
                                ),
                                user,
                            ):
                                if self.id_tag == User.chat_id:
                                    person_duty["chat_id"] = record.chat_id
                                elif self.id_tag == User.vk_id:
                                    person_duty["chat_id"] = record.vk_id
                                person_duty["name"] = user["name"]
                                person_duty["by_father_name"] = user["by_father_name"]
                else:
                    continue
            return converted_table_data
