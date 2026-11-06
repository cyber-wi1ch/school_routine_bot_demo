from collections.abc import Sequence

from telebot import types
from vkbottle import Keyboard, KeyboardButtonColor, Text

from school_routine_bot.matcher_school_bot_users import MatcherSchoolBotUsers
from school_routine_bot.pydantic_schemes import StudentFromSheet
from school_routine_bot.roles import UserRoles, get_user_roles

tg_matcher = MatcherSchoolBotUsers("tg")
vk_matcher = MatcherSchoolBotUsers("vk")


class ButtonText:
    REGISTER = "Зарегистрироваться"
    NEAREST_DUTIES = "Ближайшие дежурства"
    USER_DATA = "Ваши данные"
    BEGIN_DUTY = "Начать дежурство"
    BOT_INFO = "Информация о боте"
    REPORT_ERROR = "Сообщить об ошибке"

    ADMIN_ADD_LATE_CATCHER = "Добавить в дежурные по опозданиям"
    ADMIN_REMOVE_LATE_CATCHER = "Удалить из дежурных по опозданиям"
    ADMIN_LIST_LATE_CATCHERS = "Список дежурных по опозданиям"
    EXIT_ADMIN = "Выйти из админки"

    CANCEL = "Отмена"
    KEEP_NAME = "Оставить так"
    EDIT_NAME = "Исправить данные"

    FINISH_DUTY = "Завершить дежурство"
    BUILDING_1 = "Корпус А"
    BUILDING_2 = "Корпус Б"


# TG keyboards
def build_tg_main_keyboard(chat_id: int):
    roles = get_user_roles(chat_id, tg_matcher.id_tag)
    main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if UserRoles.NOT_FOUND in roles:
        main_markup.row(types.KeyboardButton(ButtonText.REGISTER))
        return main_markup

    main_markup.row(types.KeyboardButton(ButtonText.NEAREST_DUTIES))
    main_markup.row(types.KeyboardButton(ButtonText.USER_DATA))

    if UserRoles.LATE_CATCHER in roles:
        main_markup.row(types.KeyboardButton(ButtonText.BEGIN_DUTY))

    main_markup.row(types.KeyboardButton(ButtonText.BOT_INFO))
    main_markup.row(types.InlineKeyboardButton(ButtonText.REPORT_ERROR))

    return main_markup


def build_tg_admin_keyboard():
    admin_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    admin_markup.row(types.KeyboardButton(ButtonText.ADMIN_ADD_LATE_CATCHER))
    admin_markup.row(types.KeyboardButton(ButtonText.ADMIN_REMOVE_LATE_CATCHER))
    admin_markup.row(types.KeyboardButton(ButtonText.ADMIN_LIST_LATE_CATCHERS))
    admin_markup.row(types.KeyboardButton(ButtonText.EXIT_ADMIN))

    return admin_markup


def build_tg_admin_cancel_keyboard():
    admin_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    admin_markup.row(types.KeyboardButton(ButtonText.CANCEL))

    return admin_markup


def build_tg_edit_name_keyboard():
    editing_name_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    editing_name_markup.row(types.KeyboardButton(ButtonText.KEEP_NAME))
    editing_name_markup.row(types.KeyboardButton(ButtonText.EDIT_NAME))

    return editing_name_markup


def build_tg_building_choice_keyboard():
    building_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    building_markup.row(types.KeyboardButton(ButtonText.BUILDING_1))
    building_markup.row(types.KeyboardButton(ButtonText.BUILDING_2))
    building_markup.row(types.KeyboardButton(ButtonText.CANCEL))

    return building_markup


def build_tg_morning_duty_keyboard():
    duty_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    duty_markup.row(types.KeyboardButton(ButtonText.FINISH_DUTY))

    return duty_markup


def build_tg_choose_student_keyboard(students: Sequence[StudentFromSheet]):
    student_variants_markup = types.InlineKeyboardMarkup()

    for index, student in enumerate(students):
        student_variants_markup.add(
            types.InlineKeyboardButton(
                text=f"{student.full_name}, {student.grade}{student.letter}",
                callback_data=f"morning_duty_student:{index}",
            )
        )

    student_variants_markup.add(
        types.InlineKeyboardButton(
            text=ButtonText.CANCEL,
            callback_data="morning_duty_student_cancel",
        )
    )

    return student_variants_markup


def build_tg_late_arrival_reason_keyboard():
    late_arrival_reason_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    late_arrival_reason_markup.row(types.KeyboardButton(ButtonText.CANCEL))

    return late_arrival_reason_markup


# VK keyboards
def build_vk_main_keyboard(chat_id: int) -> Keyboard:
    roles = get_user_roles(chat_id, vk_matcher.id_tag)
    keyboard = Keyboard(one_time=False)

    if UserRoles.NOT_FOUND in roles:
        keyboard.add(Text(ButtonText.REGISTER), color=KeyboardButtonColor.PRIMARY)
        return keyboard

    keyboard.add(
        Text(ButtonText.NEAREST_DUTIES),
        color=KeyboardButtonColor.PRIMARY,
    ).row()
    keyboard.add(Text(ButtonText.USER_DATA), color=KeyboardButtonColor.SECONDARY)

    if UserRoles.LATE_CATCHER in roles:
        keyboard.add(
            Text(ButtonText.BEGIN_DUTY),
            color=KeyboardButtonColor.POSITIVE,
        ).row()
    else:
        keyboard.row()

    keyboard.add(Text(ButtonText.BOT_INFO), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text(ButtonText.REPORT_ERROR), color=KeyboardButtonColor.NEGATIVE)

    return keyboard


def build_vk_admin_keyboard() -> Keyboard:
    keyboard = Keyboard(one_time=False)
    keyboard.add(
        Text(ButtonText.ADMIN_ADD_LATE_CATCHER),
        color=KeyboardButtonColor.POSITIVE,
    ).row()
    keyboard.add(
        Text(ButtonText.ADMIN_REMOVE_LATE_CATCHER),
        color=KeyboardButtonColor.NEGATIVE,
    ).row()
    keyboard.add(
        Text(ButtonText.ADMIN_LIST_LATE_CATCHERS),
        color=KeyboardButtonColor.PRIMARY,
    ).row()
    keyboard.add(Text(ButtonText.EXIT_ADMIN), color=KeyboardButtonColor.SECONDARY)

    return keyboard


def build_vk_admin_cancel_keyboard() -> Keyboard:
    keyboard = Keyboard(one_time=False)
    keyboard.add(Text(ButtonText.CANCEL), color=KeyboardButtonColor.SECONDARY)

    return keyboard


def build_vk_edit_name_keyboard() -> Keyboard:
    keyboard = Keyboard(one_time=False)
    keyboard.add(Text(ButtonText.KEEP_NAME), color=KeyboardButtonColor.POSITIVE).row()
    keyboard.add(Text(ButtonText.EDIT_NAME), color=KeyboardButtonColor.NEGATIVE)

    return keyboard


def build_vk_building_choice_keyboard() -> Keyboard:
    keyboard = Keyboard(one_time=False)
    keyboard.add(Text(ButtonText.BUILDING_1), color=KeyboardButtonColor.PRIMARY).row()
    keyboard.add(Text(ButtonText.BUILDING_2), color=KeyboardButtonColor.PRIMARY).row()
    keyboard.add(Text(ButtonText.CANCEL), color=KeyboardButtonColor.SECONDARY)

    return keyboard


def build_vk_morning_duty_keyboard() -> Keyboard:
    keyboard = Keyboard(one_time=False)
    keyboard.add(Text(ButtonText.FINISH_DUTY), color=KeyboardButtonColor.NEGATIVE)

    return keyboard


def format_vk_student_button_label(student: StudentFromSheet) -> str:
    label = f"{student.full_name}, {student.grade}{student.letter}"
    return label[:39] + "…" if len(label) > 40 else label


def build_vk_choose_student_keyboard(students: Sequence[StudentFromSheet]) -> Keyboard:
    keyboard = Keyboard(one_time=False)

    for index, student in enumerate(students):
        label = format_vk_student_button_label(student)
        payload = None
        if label != f"{student.full_name}, {student.grade}{student.letter}":
            payload = {"student_index": index}

        keyboard.add(
            Text(label, payload=payload),
            color=KeyboardButtonColor.PRIMARY,
        ).row()

    keyboard.add(Text(ButtonText.CANCEL), color=KeyboardButtonColor.SECONDARY)

    return keyboard


def build_vk_late_arrival_reason_keyboard() -> Keyboard:
    keyboard = Keyboard(one_time=False)
    keyboard.add(Text(ButtonText.CANCEL), color=KeyboardButtonColor.SECONDARY)

    return keyboard
