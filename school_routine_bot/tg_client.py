from datetime import date, datetime
from pathlib import Path

from loguru import logger
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_helper import ApiTelegramException
from telebot.types import ReplyKeyboardRemove

from school_routine_bot.bot_keyboards import (
    ButtonText,
    build_tg_admin_cancel_keyboard,
    build_tg_admin_keyboard,
    build_tg_building_choice_keyboard,
    build_tg_choose_student_keyboard,
    build_tg_edit_name_keyboard,
    build_tg_late_arrival_reason_keyboard,
    build_tg_main_keyboard,
    build_tg_morning_duty_keyboard,
)
from school_routine_bot.db_files.db_create import get_session
from school_routine_bot.db_files.db_models import User
from school_routine_bot.duty_utils_for_bot_clients import (
    filter_personal_duty_data_for_now,
    format_actual_duty_button_text,
    make_actual_duty_message_for_person,
)
from school_routine_bot.google_sheets_morning_duty import (
    find_students_by_surname,
    get_students,
    save_late_student_record,
)
from school_routine_bot.google_sheets_polling import (
    actual_duty_data_for_both_worksheets,
)
from school_routine_bot.late_catcher_notifications import (
    notify_user_if_late_catcher_role_changed,
)
from school_routine_bot.matcher_school_bot_users import MatcherSchoolBotUsers
from school_routine_bot.morning_duty_sessions import (
    finish_morning_duty_session,
    get_morning_duty_session_info,
    start_morning_duty_session,
)
from school_routine_bot.pydantic_schemes import StudentFromSheet
from school_routine_bot.roles import (
    LATE_CATCHER_ADDED_RESULT,
    LATE_CATCHER_REMOVED_RESULT,
    UserRoles,
    add_late_catcher_by_full_name,
    get_late_catchers_list,
    get_user_id_by_messenger_id,
    get_user_roles,
    is_admin,
    remove_late_catcher_by_full_name,
)
from school_routine_bot.school_scheduler import (
    handle_the_russian_letter_e_with_dots_in_name,
    turn_english_alike_letters_into_russian,
)
from school_routine_bot.settings import get_settings

settings = get_settings()

bot = AsyncTeleBot(settings.bot_token.get_secret_value())

with open(Path(__file__).parent / "bot_info.txt") as f:
    bot_info_text = f.read()

matcher = MatcherSchoolBotUsers("tg")

TG_MAX_STUDENT_OPTIONS = 30

users_states: dict = {}

student_options_by_chat: dict[int, list[StudentFromSheet]] = {}
late_record_draft_by_chat: dict[int, dict[str, str]] = {}

STATE_ASK_FULL_NAME = 1
STATE_WRITTEN = 2

STATE_ADMIN_ADD_LATE_CATCHER = 3
STATE_ADMIN_REMOVE_LATE_CATCHER = 4

STATE_MORNING_DUTY_CHOOSE_BUILDING = 5
STATE_MORNING_DUTY_WAIT_SURNAME = 6
STATE_MORNING_DUTY_WAIT_REASON = 7


MAIN_MENU_BUTTON_TEXTS = [
    ButtonText.NEAREST_DUTIES.lower(),
    ButtonText.BOT_INFO.lower(),
    ButtonText.REPORT_ERROR.lower(),
    ButtonText.USER_DATA.lower(),
    ButtonText.BEGIN_DUTY.lower(),
    ButtonText.EXIT_ADMIN.lower(),
    ButtonText.ADMIN_ADD_LATE_CATCHER.lower(),
    ButtonText.ADMIN_REMOVE_LATE_CATCHER.lower(),
    ButtonText.ADMIN_LIST_LATE_CATCHERS.lower(),
]


def update_users_states():
    with get_session() as session:
        for user in session.query(User).all():
            users_states[user.chat_id] = STATE_WRITTEN
        logger.success(f"Known users: {list(users_states)}")

    # with open(settings.user_base_file) as f:
    #     written_users = json.load(f)
    # for chat_id in written_users:
    #     users_states[int(chat_id)] = STATE_WRITTEN
    # logger.success(f"Known users: {list(users_states)}")


async def show_buttons_to_edit_name(message):
    full_name = matcher.get_user_full_name_by_id(message.chat.id)
    if full_name:
        await bot.send_message(
            message.chat.id,
            f"Ваше ФИО: {full_name}",
            reply_markup=build_tg_edit_name_keyboard(),
        )


@bot.message_handler(
    func=lambda message: message.text in [ButtonText.KEEP_NAME, ButtonText.EDIT_NAME]
)
async def on_click_when_show_user_name(message):
    if message.text.lower() == ButtonText.KEEP_NAME.lower():
        await show_buttons_bar(message)
    elif message.text.lower() == ButtonText.EDIT_NAME.lower():
        users_states[message.chat.id] = STATE_ASK_FULL_NAME
        await bot.send_message(
            message.chat.id,
            "Впишите свое полное имя по такому шаблону: Иванов Иван Иванович",
        )


@bot.message_handler(commands=["start"])
async def start(message):
    roles = get_user_roles(message.chat.id, matcher.id_tag)
    keyboard = (
        ReplyKeyboardRemove()
        if UserRoles.NOT_FOUND in roles
        else build_tg_main_keyboard(message.chat.id)
    )
    await bot.reply_to(
        message,
        "Здравствуйте! 👋🏻 Я Ваш бот-помощник."
        " Давайте познакомимся, чтобы я смог уведомлять Вас о дежурствах."
        " Введите Ваше ФИО в следующем формате: Иванов Иван Иванович",
        reply_markup=keyboard,
    )
    users_states[message.chat.id] = STATE_ASK_FULL_NAME


@bot.message_handler(commands=["admin_mode", "admin"])
async def admin_mode(message):
    if not is_admin(message.chat.id, matcher.id_tag):
        logger.warning(f"TG user {message.chat.id} tried to enter admin mode")
        return

    await bot.send_message(
        message.chat.id,
        "Вы в админке",
        reply_markup=build_tg_admin_keyboard(),
    )


async def show_buttons_bar(message):
    await bot.send_message(
        message.chat.id,
        "📝Если Вы хотите посмотреть дежурства, на которые Вы назначены в ближайшем будущем (сегодня-завтра), "
        "кликните кнопку 'Ближайшие дежурства'. \n\n"
        "📸Чтобы проверить, корректно ли имя, которое я запомнил, "
        "кликните - 'Ваши данные'.\n"
        "\n"
        "🤖Чтобы лучше понимать, как я работаю, можете ознакомиться "
        "с информацией обо мне, "
        "кликнув -'Информация о боте.'\n"
        "\n"
        "🚨Если нашли ошибку в моей работе, кнопка "
        "'Сообщить об ошибке' может Вам помочь.",
        reply_markup=build_tg_main_keyboard(
            message.chat.id
        ),  # Build markup on demand using the message chat id.
        parse_mode="html",
    )


# Late catchers helpers
@bot.message_handler(
    func=lambda message: (
        users_states.get(message.chat.id) == STATE_ADMIN_ADD_LATE_CATCHER
    )
)
async def handle_late_catcher_full_name_from_admin(message):
    if not is_admin(message.chat.id, matcher.id_tag):
        logger.warning(
            f"TG user {message.chat.id} tried to add late_catcher without admin role"
        )
        await show_buttons_bar(message)
        return

    if message.text.lower() == ButtonText.CANCEL.lower():
        users_states[message.chat.id] = STATE_WRITTEN
        await bot.send_message(
            message.chat.id,
            "Добавление в дежурные по опозданиям отменено",
            reply_markup=build_tg_admin_keyboard(),
        )
        return

    result_message = add_late_catcher_by_full_name(message.text)
    logger.info(
        f"TG admin {message.chat.id} tried to add late_catcher: {result_message}"
    )

    if result_message == LATE_CATCHER_ADDED_RESULT:
        users_states[message.chat.id] = STATE_WRITTEN
        reply_markup = build_tg_admin_keyboard()
    else:
        reply_markup = build_tg_admin_cancel_keyboard()

    await bot.send_message(
        message.chat.id,
        result_message,
        reply_markup=reply_markup,
    )

    await notify_user_if_late_catcher_role_changed(result_message, message.text)


@bot.message_handler(
    func=lambda message: (
        users_states.get(message.chat.id) == STATE_ADMIN_REMOVE_LATE_CATCHER
    )
)
async def handle_remove_late_catcher_full_name_from_admin(message):
    if not is_admin(message.chat.id, matcher.id_tag):
        logger.warning(
            f"TG user {message.chat.id} tried to remove late_catcher without admin role"
        )
        await show_buttons_bar(message)
        return

    if message.text.lower() == ButtonText.CANCEL.lower():
        users_states[message.chat.id] = STATE_WRITTEN
        await bot.send_message(
            message.chat.id,
            "Удаление из дежурных по опозданиям отменено",
            reply_markup=build_tg_admin_keyboard(),
        )
        return

    result_message = remove_late_catcher_by_full_name(message.text)
    logger.info(
        f"TG admin {message.chat.id} tried to remove late_catcher: {result_message}"
    )

    if result_message == LATE_CATCHER_REMOVED_RESULT:
        users_states[message.chat.id] = STATE_WRITTEN
        reply_markup = build_tg_admin_keyboard()
    else:
        reply_markup = build_tg_admin_cancel_keyboard()

    await bot.send_message(
        message.chat.id,
        result_message,
        reply_markup=reply_markup,
    )

    await notify_user_if_late_catcher_role_changed(result_message, message.text)


@bot.message_handler(
    func=lambda message: (
        users_states.get(message.chat.id) == STATE_ASK_FULL_NAME
        and message.text.lower()
        not in [
            *MAIN_MENU_BUTTON_TEXTS,
            ButtonText.REGISTER.lower(),
            "start",
            "admin",
            "help",
            "info",
        ]
        and not message.text.lstrip().startswith("/")
    )
)
async def get_full_name(message):
    user_full_name = str(turn_english_alike_letters_into_russian(message.text))
    saved = matcher.write_full_name_into_user_base(message.chat.id, user_full_name)

    if not saved:
        await bot.send_message(
            message.chat.id,
            "Не удалось сохранить Ваши данные. "
            "Проверьте правильность ФИО. "
            "Попробуйте еще раз. "
            "Если ФИО указаны верно и повторная попытка не сработала, обратитесь к администратору "
            "бота.",
        )
        return
    users_states[message.chat.id] = STATE_WRITTEN  # Exit the state.
    await bot.send_message(
        message.chat.id,
        f"Приятно с Вами познакомиться, "
        f"{matcher.get_user_full_name_by_id(message.chat.id)}! "
        f"Теперь я могу сообщать Вам о дежурствах! ✅",
    )
    await show_buttons_bar(message)


async def start_add_late_catcher_mode(message):
    if not is_admin(message.chat.id, matcher.id_tag):
        await show_buttons_bar(message)
        return

    users_states[message.chat.id] = STATE_ADMIN_ADD_LATE_CATCHER
    await bot.send_message(
        message.chat.id,
        "Введите полное имя пользователя.",
        reply_markup=build_tg_admin_cancel_keyboard(),
    )


async def start_remove_late_catcher_mode(message):
    if not is_admin(message.chat.id, matcher.id_tag):
        await show_buttons_bar(message)
        return

    users_states[message.chat.id] = STATE_ADMIN_REMOVE_LATE_CATCHER
    await bot.send_message(
        message.chat.id,
        "Внимание! Вы собираетесь удалить пользователя из дежурных по опозданиям! "
        "Введите полное имя пользователя.",
        reply_markup=build_tg_admin_cancel_keyboard(),
    )


async def show_late_catchers_list(message):
    if not is_admin(message.chat.id, matcher.id_tag):
        await show_buttons_bar(message)
        return

    await bot.send_message(
        message.chat.id,
        get_late_catchers_list(),
        reply_markup=build_tg_admin_keyboard(),
    )


# Morning duty helpers
async def start_morning_duty_mode(message):
    if UserRoles.LATE_CATCHER not in get_user_roles(message.chat.id, matcher.id_tag):
        logger.info("late_catcher isn't found")
        await show_buttons_bar(message)
        return

    users_states[message.chat.id] = STATE_MORNING_DUTY_CHOOSE_BUILDING

    await bot.send_message(
        message.chat.id,
        "Пожалуйста, проводите одно утреннее дежурство только в одном мессенджере. "
        "Иначе возникнут дубли записей в таблице.\n\n"
        "Если TG-бот перестал отвечать, перейдите в VK-версию и кликните 'Начать дежурство'. "
        "Продолжайте работу там до конца дежурства.",
    )

    await bot.send_message(
        message.chat.id,
        "Выберите адрес",
        reply_markup=build_tg_building_choice_keyboard(),
    )


async def finish_morning_duty_mode(message):
    user_id = get_user_id_by_messenger_id(
        messenger_id=message.chat.id,
        messenger_id_tag=matcher.id_tag,
    )

    if user_id is None:
        users_states[message.chat.id] = STATE_WRITTEN
        await show_buttons_bar(message)
        return

    finished_session_id = finish_morning_duty_session(
        late_catcher_user_id=user_id,
        duty_date=date.today(),
        finished_at=datetime.now(),
    )

    users_states[message.chat.id] = STATE_WRITTEN

    if finished_session_id is None:
        await bot.send_message(
            message.chat.id,
            "Не найдено начатое дежурство.",
            reply_markup=build_tg_main_keyboard(message.chat.id),
        )
        return

    await bot.send_message(
        message.chat.id,
        "Дежурство завершено.",
        reply_markup=build_tg_main_keyboard(message.chat.id),
    )


def get_morning_duty_session_for_message(message):
    user_id = get_user_id_by_messenger_id(
        messenger_id=message.chat.id,
        messenger_id_tag=matcher.id_tag,
    )

    if user_id is None:
        return None

    return get_morning_duty_session_info(
        late_catcher_user_id=user_id,
        duty_date=date.today(),
    )


@bot.message_handler(
    func=lambda message: (
        users_states.get(message.chat.id) == STATE_MORNING_DUTY_CHOOSE_BUILDING
    )
)
async def handle_morning_duty_building_choice(message):
    if message.text.lower() == ButtonText.CANCEL.lower():
        users_states[message.chat.id] = STATE_WRITTEN
        await bot.send_message(
            message.chat.id,
            "Дежурство не будет записано.",
            reply_markup=build_tg_main_keyboard(message.chat.id),
        )
        return

    if message.text not in [ButtonText.BUILDING_1, ButtonText.BUILDING_2]:
        await bot.send_message(
            message.chat.id,
            "Выберите адрес кнопкой",
            reply_markup=build_tg_building_choice_keyboard(),
        )
        return

    user_id = get_user_id_by_messenger_id(
        messenger_id=message.chat.id,
        messenger_id_tag=matcher.id_tag,
    )

    if user_id is None:
        users_states[message.chat.id] = STATE_WRITTEN
        await show_buttons_bar(message)
        return

    late_catcher_full_name = matcher.get_user_full_name_by_id(message.chat.id)

    start_morning_duty_session(
        late_catcher_user_id=user_id,
        late_catcher_full_name=late_catcher_full_name,
        duty_date=date.today(),
        building_address=message.text,
        started_at=datetime.now(),
    )

    users_states[message.chat.id] = STATE_MORNING_DUTY_WAIT_SURNAME

    await bot.send_message(
        message.chat.id,
        "Дежурство началось. Введите фамилию опоздавшего.",
        reply_markup=build_tg_morning_duty_keyboard(),
    )


async def handle_late_student_surname(message):
    found_students = find_students_by_surname(get_students(), message.text)

    if not found_students:
        await bot.send_message(
            message.chat.id,
            "Ученик с такой фамилией не найден. Попробуйте другой вариант.",
            reply_markup=build_tg_morning_duty_keyboard(),
        )
        return

    if len(found_students) > TG_MAX_STUDENT_OPTIONS:
        await bot.send_message(
            message.chat.id,
            "Найдено слишком много учеников с такой фамилией. "
            "Введите фамилию и имя или полное ФИО.",
            reply_markup=build_tg_morning_duty_keyboard(),
        )
        return

    student_options_by_chat[message.chat.id] = found_students

    await bot.send_message(
        message.chat.id,
        "Выберите ученика:",
        reply_markup=build_tg_choose_student_keyboard(found_students),
    )


@bot.callback_query_handler(
    func=lambda call: call.data == "morning_duty_student_cancel"
)
async def handle_morning_duty_student_choice_cancel(call):
    chat_id = call.message.chat.id

    student_options_by_chat.pop(chat_id, None)
    late_record_draft_by_chat.pop(chat_id, None)

    users_states[chat_id] = STATE_MORNING_DUTY_WAIT_SURNAME

    await bot.send_message(
        chat_id,
        "Введите фамилию опоздавшего.",
        reply_markup=build_tg_morning_duty_keyboard(),
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("morning_duty_student:")
)
async def handle_morning_duty_student_choice(call):
    chat_id = call.message.chat.id
    if users_states.get(chat_id) != STATE_MORNING_DUTY_WAIT_SURNAME:
        return

    student_index = int(call.data.split(":")[1])

    students = student_options_by_chat.get(chat_id)

    if not students or student_index < 0 or student_index >= len(students):
        users_states[chat_id] = STATE_MORNING_DUTY_WAIT_SURNAME
        await bot.send_message(
            chat_id,
            "Не удалось найти выбранный вариант. Введите фамилию еще раз.",
            reply_markup=build_tg_morning_duty_keyboard(),
        )
        return

    selected_student = students[student_index]

    late_record_draft_by_chat[chat_id] = {
        "late_student_full_name": selected_student.full_name,
        "grade": selected_student.grade,
        "letter": selected_student.letter,
    }

    users_states[chat_id] = STATE_MORNING_DUTY_WAIT_REASON

    await bot.send_message(
        chat_id,
        f"Выбран ученик: {selected_student.full_name}, "
        f"{selected_student.grade}{selected_student.letter}.\n"
        "Введите причину опоздания (если ее нет, так и запишите) или нажмите 'Отмена'.",
        reply_markup=build_tg_late_arrival_reason_keyboard(),
    )


async def cancel_late_student_choice(message):
    late_record_draft_by_chat.pop(message.chat.id, None)

    students = student_options_by_chat.get(message.chat.id)
    users_states[message.chat.id] = STATE_MORNING_DUTY_WAIT_SURNAME

    if students:
        await bot.send_message(
            message.chat.id,
            "Выберите ученика:",
            reply_markup=build_tg_choose_student_keyboard(students),
        )
        return

    await bot.send_message(
        message.chat.id,
        "Введите фамилию опоздавшего.",
        reply_markup=build_tg_morning_duty_keyboard(),
    )


async def save_late_arrival_reason(message, draft, morning_duty_session):
    await save_late_student_record(
        morning_duty_session=morning_duty_session,
        late_student_full_name=draft["late_student_full_name"],
        grade=draft["grade"],
        letter=draft["letter"],
        late_date=date.today(),
        late_time=datetime.now().time(),
        reason=message.text,
    )

    student_options_by_chat.pop(message.chat.id, None)
    late_record_draft_by_chat.pop(message.chat.id, None)

    users_states[message.chat.id] = STATE_MORNING_DUTY_WAIT_SURNAME

    await bot.send_message(
        message.chat.id,
        "Опоздание записано. Введите следующую фамилию.",
        reply_markup=build_tg_morning_duty_keyboard(),
    )


@bot.message_handler(
    func=lambda message: (
        users_states.get(message.chat.id) == STATE_MORNING_DUTY_WAIT_REASON
    )
)
async def handle_morning_duty_wait_reason(message):
    if message.text.lower() == ButtonText.CANCEL.lower():
        await cancel_late_student_choice(message)
        return

    draft = late_record_draft_by_chat.get(message.chat.id)
    morning_duty_session = get_morning_duty_session_for_message(message)

    if draft is None or morning_duty_session is None:
        late_record_draft_by_chat.pop(message.chat.id, None)
        users_states[message.chat.id] = STATE_MORNING_DUTY_WAIT_SURNAME

        await bot.send_message(
            message.chat.id,
            "Не удалось сохранить опоздание. Введите фамилию еще раз.",
            reply_markup=build_tg_morning_duty_keyboard(),
        )
        return

    await bot.send_message(
        message.chat.id,
        "Подождите, опоздание записывается...",
    )

    await save_late_arrival_reason(message, draft, morning_duty_session)


@bot.message_handler(
    func=lambda message: (
        users_states.get(message.chat.id) == STATE_MORNING_DUTY_WAIT_SURNAME
    )
)
async def handle_morning_duty_wait_surname(message):
    if message.text.lower() == ButtonText.FINISH_DUTY.lower():
        await finish_morning_duty_mode(message)
        return

    if message.text.lower() in MAIN_MENU_BUTTON_TEXTS:
        await bot.send_message(
            message.chat.id,
            "Эта команда не доступна в данном режиме.\n"
            "Введите фамилию опоздавшего или нажмите 'Завершить дежурство'.",
            reply_markup=build_tg_morning_duty_keyboard(),
        )
        return

    await handle_late_student_surname(message)


@bot.message_handler(
    func=lambda message: (
        message.text.lower()
        in [
            ButtonText.NEAREST_DUTIES.lower(),
            ButtonText.BOT_INFO.lower(),
            ButtonText.REPORT_ERROR.lower(),
            ButtonText.USER_DATA.lower(),
            ButtonText.BEGIN_DUTY.lower(),
            ButtonText.EXIT_ADMIN.lower(),
            ButtonText.ADMIN_ADD_LATE_CATCHER.lower(),
            ButtonText.ADMIN_LIST_LATE_CATCHERS.lower(),
            ButtonText.ADMIN_REMOVE_LATE_CATCHER.lower(),
        ]
    )
)
async def on_click(
    message,
):  # Add an extra-user button later and keep its checks in a separate module.
    users_states[message.chat.id] = STATE_WRITTEN
    username = matcher.get_user_full_name_by_id(message.chat.id)

    if message.text.lower() == ButtonText.BOT_INFO.lower():
        await bot.send_message(message.chat.id, bot_info_text, parse_mode="html")

    elif message.text.lower() == ButtonText.BEGIN_DUTY.lower():
        await start_morning_duty_mode(message)

    elif message.text.lower() == ButtonText.EXIT_ADMIN.lower():
        await show_buttons_bar(message)

    elif message.text.lower() == ButtonText.ADMIN_ADD_LATE_CATCHER.lower():
        await start_add_late_catcher_mode(message)

    elif message.text.lower() == ButtonText.ADMIN_REMOVE_LATE_CATCHER.lower():
        await start_remove_late_catcher_mode(message)

    elif message.text.lower() == ButtonText.ADMIN_LIST_LATE_CATCHERS.lower():
        await show_late_catchers_list(message)

    elif message.text.lower() == ButtonText.REPORT_ERROR.lower():
        logger.warning(f"User {message.chat.id} {username} tried to tell on us")
        await bot.send_message(
            message.chat.id,
            "Сообщите об ошибке ответственному за работу бота.",
        )

    elif message.text.lower() == ButtonText.USER_DATA.lower():
        await show_buttons_to_edit_name(message)

    elif message.text.lower() == ButtonText.NEAREST_DUTIES.lower():
        personal_duty_message = ""

        surname = handle_the_russian_letter_e_with_dots_in_name(
            str(username.split(" ")[0]).lower()
        )
        for sorted_worksheet_data in actual_duty_data_for_both_worksheets:
            duty_info = make_actual_duty_message_for_person(
                surname.lower(),
                filter_personal_duty_data_for_now(
                    actual_duty_data_for_both_worksheets[sorted_worksheet_data]
                ),
                message.chat.id,
            )
            personal_duty_message += (
                f"<i>(Из листа таблицы "
                f"'{sorted_worksheet_data}')</i>\n "
                f"{duty_info}"
            )

        if personal_duty_message == "" or "ДАТА" not in personal_duty_message:
            personal_duty_message = (
                "🔴 Кажется, у Вас нет ближайших дежурств (сегодня-завтра).\n\n "
                "<i>(Если это противоречит действительности, пожалуйста, "
                "попробуйте кликнуть на кнопку через несколько минут. "
                "Вероятно, данные из таблицы еще не успели подтянуться. Благодарю за понимание! ☀️)</i>"
            )

        else:
            formatted_message = format_actual_duty_button_text(personal_duty_message)
            personal_duty_message = (
                f"{formatted_message}\n\n <i>(❣️Если Вы только что "
                f"записались на дежурство или отменили его "
                f"в таблице, пожалуйста, "
                f"кликните кнопку через пару минут, "
                f"- так бот точно успеет подтянуть "
                f"изменения из таблицы.)</i>"
            )

        logger.warning(
            f"User {message.chat.id} {username} "
            f"has following actual duties:\n{personal_duty_message}"
        )

        await bot.send_message(
            message.chat.id, personal_duty_message, parse_mode="html"
        )


@bot.message_handler(
    func=lambda message: (
        users_states.get(message.chat.id) == STATE_WRITTEN
        and message.text.lower()
        not in [
            ButtonText.NEAREST_DUTIES.lower(),
            ButtonText.BOT_INFO.lower(),
            ButtonText.REPORT_ERROR.lower(),
            ButtonText.USER_DATA.lower(),
            ButtonText.BEGIN_DUTY.lower(),
            ButtonText.EXIT_ADMIN.lower(),
            ButtonText.ADMIN_ADD_LATE_CATCHER.lower(),
            ButtonText.ADMIN_REMOVE_LATE_CATCHER.lower(),
            ButtonText.ADMIN_LIST_LATE_CATCHERS.lower(),
        ]
    )
)
async def handle_any_message(message):
    await show_buttons_bar(message)


async def announce_about_changes():
    """
    Notify all database users with a Telegram ID about
    the VK bot launch and the updated button.
    """
    with get_session() as session:
        # Get all users with a non-empty tg_id.
        users = session.query(User).filter(User.chat_id.is_not(None)).all()

        for user in users:
            try:
                # bot.send_message should be sync here, e.g. python-telegram-bot before v20.
                await bot.send_message(
                    user.chat_id,
                    "Здравствуй, дорогой пользователь! 👋🏻\n\n"
                    "Напоминаем: теперь наш бот доступен и ВКонтакте! 📲  "
                    "Чтобы начать работу с ВК-версией School Routine Bot, "
                    "<b>пройдите несколько шагов, перечисленных ниже.</b>\n\n"
                    " 1. <b>Откройте ВК-сообщество бота</b>, указанное вашей школой.\n\n "
                    "<i>(☝️Не забудьте выключить впн после перехода по ссылке, если он включен, "
                    "так как могут возникнуть сложности с регистрацией в ВК боте.)</i>\n\n"
                    " 2. На странице сообщества ВК "
                    " <b>кликните на 'Сообщения' или 'Messages'</b>. Так Вы перейдете в чат с нашим ботом.\n\n"
                    " 3. Нажмите кнопку <b>'Начать'</b>.\n\n"
                    " 4. <b>Введите свое полное ФИО.</b> <i>(Ваши данные должны быть записаны так же, "
                    "как и в Telegram-версии).</i>\n\n"
                    " 5. 🎉 Отлично! Теперь Вам доступны обе версии бота - Telegram и ВКонтакте.\n\n"
                    "<i><u><b>🔎 Примечание</b></u>: Бот будет предупреждать Вас о завтрашних дежурствах в 13.00, "
                    "сообщать об изменениях в назначенных дежурствах, "
                    "а также уведомлять за 15 минут до дежурства в обоих мессенджерах.</i>",
                    parse_mode="html",
                )
                logger.info(f"User {user.chat_id} (surname={user.surname}) notified")
            except ApiTelegramException:
                logger.error(f"User {user.chat_id} blocked the bot or is not available")
                continue
