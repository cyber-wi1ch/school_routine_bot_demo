from datetime import date, datetime

from loguru import logger
from vkbottle import API
from vkbottle.bot import Message
from vkbottle.tools.formatting import bold, italic

from school_routine_bot.bot_keyboards import (
    ButtonText,
    build_vk_admin_cancel_keyboard,
    build_vk_admin_keyboard,
    build_vk_building_choice_keyboard,
    build_vk_choose_student_keyboard,
    build_vk_edit_name_keyboard,
    build_vk_late_arrival_reason_keyboard,
    build_vk_main_keyboard,
    build_vk_morning_duty_keyboard,
)
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
from school_routine_bot.vk_bot.bot_info_vk import bot_info
from school_routine_bot.vk_bot.vk_states import States

settings = get_settings()
matcher = MatcherSchoolBotUsers("vk")

vk_api = API(token=settings.vk_bot_token.get_secret_value())

student_options_by_peer: dict[int, list[StudentFromSheet]] = {}
late_record_draft_by_peer: dict[int, dict[str, str]] = {}


# with open(Path(__file__).parent / "bot_info_vk.txt", 'r', encoding='utf-8') as f:
#     bot_info_text = f.read()


async def show_main_menu(message: Message):
    keyboard = build_vk_main_keyboard(message.from_id)
    menu_text = (
        "📝 Если Вы хотите посмотреть дежурства, на которые Вы назначены в ближайшем будущем (сегодня-завтра), "
        "кликните кнопку 'Ближайшие дежурства'.\n\n"
        "📸 Чтобы проверить, корректно ли имя, которое я запомнил, "
        "кликните - 'Ваши данные'.\n\n"
        "🤖 Чтобы лучше понимать, как я работаю, можете ознакомиться "
        "с информацией обо мне, "
        "кликнув - 'Информация о боте'.\n\n"
        "🚨 Если нашли ошибку в моей работе, кнопка "
        "'Сообщить об ошибке' может Вам помочь."
    )
    await message.answer(menu_text, keyboard=keyboard)


def clean_up_html_symbols(message: str) -> str:
    message = message.replace("<b>", "")
    message = message.replace("</b>", "")
    message = message.replace("<i>", "")
    message = message.replace("</i>", "")
    message = message.replace("<u>", "")
    message = message.replace("</u>", "")
    return message


def text_matches_button(message_text: str | None, button_text: str) -> bool:
    return bool(message_text and message_text.lower() == button_text.lower())


def text_equals_button(button_text: str):
    def matches_message(message):
        return text_matches_button(message.text, button_text)

    return matches_message


async def delete_state_if_exists(bot, peer_id: int):
    try:
        await bot.state_dispenser.delete(peer_id)
    except KeyError:
        return


button_texts = [
    value.lower()
    for name, value in vars(ButtonText).items()
    if not name.startswith("_") and isinstance(value, str)
]


def setup_handlers(bot):
    """Register all handlers."""

    # ---- Start ----
    @bot.on.message(func=lambda m: m.text and m.text.lower() in ["start", "начать"])
    async def start(message: Message):
        await bot.state_dispenser.set(message.peer_id, States.ASK_FULL_NAME)
        await message.answer(
            "Здравствуйте! 👋🏻 Я Ваш бот-помощник. "
            "Давайте познакомимся, чтобы я смог уведомлять Вас о дежурствах. "
            "Введите Ваше ФИО в следующем формате: Иванов Иван Иванович"
        )

    # ---- Hidden admin mode ----
    @bot.on.message(
        func=lambda m: m.text
        and m.text.lower() in ["/admin_mode", "/admin", "admin_mode", "admin"]
    )
    async def admin_mode(message: Message):
        if not is_admin(message.from_id, matcher.id_tag):
            logger.warning(f"VK user {message.from_id} tried to enter admin mode")
            return

        await delete_state_if_exists(bot, message.peer_id)
        await message.answer("Вы в админке", keyboard=build_vk_admin_keyboard())

    # ---- Full name input (ASK_FULL_NAME state) ----
    @bot.on.message(state=States.ASK_FULL_NAME)
    async def get_full_name(message: Message):
        # If a menu button is clicked, cancel input and show the menu.
        if message.text and message.text.lower() in [
            *button_texts,
            "start",
            "admin",
            "help",
            "info",
        ]:
            await delete_state_if_exists(bot, message.peer_id)
            await show_main_menu(message)
            return

        if not message.text:
            await message.answer("Пожалуйста, введите ФИО текстом.")
            return

        if message.text.lstrip().startswith("/"):
            return

        user_full_name = turn_english_alike_letters_into_russian(message.text)
        saved = matcher.write_full_name_into_user_base(message.from_id, user_full_name)

        if not saved:
            await message.answer(
                "Не удалось сохранить Ваши данные. "
                "Проверьте правильность ФИО. "
                "Попробуйте еще раз. "
                "Если ФИО указаны верно и повторная попытка не сработала, обратитесь к администратору "
                "бота.",
            )
            return
        await delete_state_if_exists(bot, message.peer_id)  # Exit the state.

        full_name = matcher.get_user_full_name_by_id(message.from_id)
        await message.answer(
            f"Приятно с Вами познакомиться, {full_name}! "
            f"Теперь я могу сообщать Вам о дежурствах! ✅"
        )
        await show_main_menu(message)

    # ---- Full name input for adding a late catcher ----
    @bot.on.message(state=States.ADMIN_ADD_LATE_CATCHER)
    async def handle_late_catcher_full_name_from_admin(message: Message):
        if not is_admin(message.from_id, matcher.id_tag):
            logger.warning(
                f"VK user {message.from_id} tried to add late_catcher without admin role"
            )
            await delete_state_if_exists(bot, message.peer_id)
            await show_main_menu(message)
            return

        if message.text and message.text.lower() == ButtonText.CANCEL.lower():
            await delete_state_if_exists(bot, message.peer_id)
            await message.answer(
                "Добавление в дежурные по опозданиям отменено",
                keyboard=build_vk_admin_keyboard(),
            )
            return

        result_message = add_late_catcher_by_full_name(message.text or "")
        logger.info(
            f"VK admin {message.from_id} tried to add late_catcher: {result_message}"
        )

        if result_message == LATE_CATCHER_ADDED_RESULT:
            await delete_state_if_exists(bot, message.peer_id)
            keyboard = build_vk_admin_keyboard()
        else:
            keyboard = build_vk_admin_cancel_keyboard()

        await message.answer(result_message, keyboard=keyboard)

        await notify_user_if_late_catcher_role_changed(
            result_message,
            message.text or "",
        )

    # ---- Full name input for removing a late catcher ----
    @bot.on.message(state=States.ADMIN_REMOVE_LATE_CATCHER)
    async def handle_remove_late_catcher_full_name_from_admin(message: Message):
        if not is_admin(message.from_id, matcher.id_tag):
            logger.warning(
                f"VK user {message.from_id} tried to remove late_catcher without admin role"
            )
            await delete_state_if_exists(bot, message.peer_id)
            await show_main_menu(message)
            return

        if message.text and message.text.lower() == ButtonText.CANCEL.lower():
            await delete_state_if_exists(bot, message.peer_id)
            await message.answer(
                "Удаление из дежурных по опозданиям отменено",
                keyboard=build_vk_admin_keyboard(),
            )
            return

        result_message = remove_late_catcher_by_full_name(message.text or "")
        logger.info(
            f"VK admin {message.from_id} tried to remove late_catcher: {result_message}"
        )

        if result_message == LATE_CATCHER_REMOVED_RESULT:
            await delete_state_if_exists(bot, message.peer_id)
            keyboard = build_vk_admin_keyboard()
        else:
            keyboard = build_vk_admin_cancel_keyboard()

        await message.answer(result_message, keyboard=keyboard)

        await notify_user_if_late_catcher_role_changed(
            result_message,
            message.text or "",
        )

    # ---- Register button (only for unregistered users) ----
    @bot.on.message(func=text_equals_button(ButtonText.REGISTER))
    # TODO check the func and the realization through show_user_data cuz it seems we have a double
    async def register(message: Message):
        if UserRoles.NOT_FOUND not in get_user_roles(message.from_id, matcher.id_tag):
            await show_main_menu(message)
        else:
            await bot.state_dispenser.set(message.peer_id, States.ASK_FULL_NAME)
            await message.answer("Введите Ваше ФИО в формате: Иванов Иван Иванович")

    # ---- Nearest duties ----
    @bot.on.message(func=text_equals_button(ButtonText.NEAREST_DUTIES))
    async def show_duties(message: Message):
        keyboard = build_vk_main_keyboard(message.from_id)
        roles = get_user_roles(message.from_id, matcher.id_tag)
        if UserRoles.NOT_FOUND in roles:
            await bot.state_dispenser.set(message.peer_id, States.ASK_FULL_NAME)
            await message.answer("Вы не зарегистрированы. Введите Ваше ФИО.")
            return

        username = matcher.get_user_full_name_by_id(message.from_id)
        if not username:
            await register(message)
            return

        personal_duty_message = ""
        surname = handle_the_russian_letter_e_with_dots_in_name(
            str(username.split(" ")[0]).lower()
        )

        for worksheet_name in actual_duty_data_for_both_worksheets:
            duty_info = make_actual_duty_message_for_person(
                surname.lower(),
                filter_personal_duty_data_for_now(
                    actual_duty_data_for_both_worksheets[worksheet_name]
                ),
                message.from_id,
            )
            personal_duty_message += (
                f"<i>(Из листа таблицы '{worksheet_name}')</i>\n {duty_info}"
                # replace html symbols with
                # the very vk formatting here and below
            )

        if not personal_duty_message or "ДАТА" not in personal_duty_message:
            personal_duty_message = (
                "🔴 Кажется, у Вас нет ближайших дежурств (сегодня-завтра).\n\n "
                + italic(
                    "(Если это противоречит действительности, пожалуйста, "
                    "попробуйте кликнуть на кнопку через несколько минут. "
                    "Вероятно, данные из таблицы еще не успели подтянуться. "
                    "Благодарю за понимание! ☀️)"
                )
            )

        else:
            formatted = clean_up_html_symbols(
                format_actual_duty_button_text(personal_duty_message)
            )
            personal_duty_message = (
                bold(formatted)
                + "\n\n"
                + italic(
                    "(❣️Если Вы только что "
                    "записались на дежурство или отменили его "
                    "в таблице, пожалуйста, "
                    "кликните кнопку через пару минут, "
                    "- так бот точно успеет подтянуть "
                    "изменения из таблицы.)"
                )
            )

        logger.info(
            f"User {message.from_id} {username} "
            f"has following actual duties:\n{personal_duty_message}"
        )

        await message.answer(personal_duty_message, keyboard=keyboard)

    # ---- User data ----
    @bot.on.message(func=text_equals_button(ButtonText.USER_DATA))  # a double?
    async def show_user_data(message: Message):
        roles = get_user_roles(message.from_id, matcher.id_tag)
        if UserRoles.NOT_FOUND in roles:
            await bot.state_dispenser.set(message.peer_id, States.ASK_FULL_NAME)
            await message.answer("Вы не зарегистрированы. Введите Ваше ФИО.")
            return

        full_name = matcher.get_user_full_name_by_id(message.from_id)
        if not full_name:
            await register(message)
            return

        await message.answer(
            f"Ваше ФИО: {full_name}",
            keyboard=build_vk_edit_name_keyboard(),
        )

    # ---- Keep name ----
    @bot.on.message(
        func=text_equals_button(ButtonText.KEEP_NAME)
    )  # one more double? or what
    async def keep_name(message: Message):
        roles = get_user_roles(message.from_id, matcher.id_tag)
        if UserRoles.NOT_FOUND in roles:
            await register(message)
            return
        await show_main_menu(message)

    # ---- Edit name ----
    @bot.on.message(func=text_equals_button(ButtonText.EDIT_NAME))
    async def edit_name(message: Message):
        roles = get_user_roles(message.from_id, matcher.id_tag)
        if UserRoles.NOT_FOUND in roles:
            await register(message)
            return
        await bot.state_dispenser.set(message.peer_id, States.ASK_FULL_NAME)
        await message.answer(
            "Впишите свое полное имя по такому шаблону: Иванов Иван Иванович"
        )

    # ---- Bot info ----
    @bot.on.message(func=text_equals_button(ButtonText.BOT_INFO))
    async def show_info(message: Message):
        await message.answer(bot_info)

    # ---- Report error ----
    @bot.on.message(func=text_equals_button(ButtonText.REPORT_ERROR))
    async def report_error(message: Message):
        username = matcher.get_user_full_name_by_id(message.from_id)
        logger.warning(f"User {message.from_id} {username} tried to report an error")
        await message.answer("Сообщите об ошибке ответственному за работу бота.")

    # ---- Start duty ----
    @bot.on.message(func=text_equals_button(ButtonText.BEGIN_DUTY))
    async def start_duty(message: Message):
        roles = get_user_roles(message.from_id, matcher.id_tag)
        if UserRoles.NOT_FOUND in roles:
            await register(message)
            return
        if UserRoles.LATE_CATCHER in roles:
            logger.info("late_catcher is found")
            await bot.state_dispenser.set(
                message.peer_id,
                States.MORNING_DUTY_CHOOSE_BUILDING,
            )

            await message.answer(
                "Пожалуйста, проводите одно утреннее дежурство только в одном мессенджере. "
                "Иначе возникнут дубли записей в таблице.\n\n"
                "Если VK-бот перестал отвечать, перейдите в TG-версию и кликните 'Начать дежурство'. "
                "Продолжайте работу там до конца дежурства."
            )

            await message.answer(
                "Выберите адрес",
                keyboard=build_vk_building_choice_keyboard(),
            )
        else:
            logger.info("late_catcher isn't found")
            await show_main_menu(message)

    @bot.on.message(state=States.MORNING_DUTY_CHOOSE_BUILDING)
    async def handle_morning_duty_building_choice(message: Message):
        if message.text and message.text.lower() == ButtonText.CANCEL.lower():
            await delete_state_if_exists(bot, message.peer_id)
            await message.answer(
                "Дежурство не будет записано.",
                keyboard=build_vk_main_keyboard(message.from_id),
            )
            return

        if message.text not in [ButtonText.BUILDING_1, ButtonText.BUILDING_2]:
            await message.answer(
                "Выберите адрес кнопкой",
                keyboard=build_vk_building_choice_keyboard(),
            )
            return

        user_id = get_user_id_by_messenger_id(
            messenger_id=message.from_id,
            messenger_id_tag=matcher.id_tag,
        )

        if user_id is None:
            await delete_state_if_exists(bot, message.peer_id)
            await show_main_menu(message)
            return

        late_catcher_full_name = matcher.get_user_full_name_by_id(message.from_id)

        start_morning_duty_session(
            late_catcher_user_id=user_id,
            late_catcher_full_name=late_catcher_full_name,
            duty_date=date.today(),
            building_address=message.text,
            started_at=datetime.now(),
        )

        await bot.state_dispenser.set(
            message.peer_id,
            States.MORNING_DUTY_WAIT_SURNAME,
        )
        await message.answer(
            "Дежурство началось. Введите фамилию опоздавшего.",
            keyboard=build_vk_morning_duty_keyboard(),
        )

    async def finish_morning_duty_mode(message: Message):
        user_id = get_user_id_by_messenger_id(
            messenger_id=message.from_id,
            messenger_id_tag=matcher.id_tag,
        )

        if user_id is None:
            await delete_state_if_exists(bot, message.peer_id)
            await show_main_menu(message)
            return

        finished_session_id = finish_morning_duty_session(
            late_catcher_user_id=user_id,
            duty_date=date.today(),
            finished_at=datetime.now(),
        )

        await delete_state_if_exists(bot, message.peer_id)

        if finished_session_id is None:
            await message.answer(
                "Не найдено начатое дежурство.",
                keyboard=build_vk_main_keyboard(message.from_id),
            )
            return

        await message.answer(
            "Дежурство завершено.",
            keyboard=build_vk_main_keyboard(message.from_id),
        )

    def get_morning_duty_session_for_message(message: Message):
        user_id = get_user_id_by_messenger_id(
            messenger_id=message.from_id,
            messenger_id_tag=matcher.id_tag,
        )

        if user_id is None:
            return None

        return get_morning_duty_session_info(
            late_catcher_user_id=user_id,
            duty_date=date.today(),
        )

    @bot.on.message(state=States.MORNING_DUTY_WAIT_SURNAME)
    async def handle_morning_duty_wait_surname(message: Message):
        if message.text and message.text.lower() == ButtonText.FINISH_DUTY.lower():
            await finish_morning_duty_mode(message)
            return

        found_students = find_students_by_surname(get_students(), message.text or "")

        if not found_students:
            await message.answer(
                "Ученик с такой фамилией не найден. Попробуйте другой вариант.",
                keyboard=build_vk_morning_duty_keyboard(),
            )
            return

        if len(found_students) > 8:
            await message.answer(
                "Найдено слишком много учеников с такой фамилией. "
                "Уточните имя или имя и отчество.",
                keyboard=build_vk_morning_duty_keyboard(),
            )
            return

        student_options_by_peer[message.peer_id] = found_students

        await bot.state_dispenser.set(
            message.peer_id,
            States.MORNING_DUTY_CHOOSE_STUDENT,
        )
        await message.answer(
            "Выберите ученика:",
            keyboard=build_vk_choose_student_keyboard(found_students),
        )

    async def cancel_student_choice(message: Message):
        student_options_by_peer.pop(message.peer_id, None)
        late_record_draft_by_peer.pop(message.peer_id, None)

        await bot.state_dispenser.set(
            message.peer_id,
            States.MORNING_DUTY_WAIT_SURNAME,
        )
        await message.answer(
            "Введите фамилию опоздавшего.",
            keyboard=build_vk_morning_duty_keyboard(),
        )

    @bot.on.message(state=States.MORNING_DUTY_CHOOSE_STUDENT)
    async def handle_morning_duty_student_choice(message: Message):
        if message.text and message.text.lower() == ButtonText.CANCEL.lower():
            await cancel_student_choice(message)
            return

        students = student_options_by_peer.get(message.peer_id)

        if not students:
            await bot.state_dispenser.set(
                message.peer_id,
                States.MORNING_DUTY_WAIT_SURNAME,
            )
            await message.answer(
                "Введите фамилию опоздавшего.",
                keyboard=build_vk_morning_duty_keyboard(),
            )
            return

        selected_student = next(
            (
                student
                for student in students
                if message.text
                == f"{student.full_name}, {student.grade}{student.letter}"
            ),
            None,
        )

        if selected_student is None:
            await message.answer(
                "Выберите ученика кнопкой.",
                keyboard=build_vk_choose_student_keyboard(students),
            )
            return

        late_record_draft_by_peer[message.peer_id] = {
            "late_student_full_name": selected_student.full_name,
            "grade": selected_student.grade,
            "letter": selected_student.letter,
        }

        await bot.state_dispenser.set(
            message.peer_id,
            States.MORNING_DUTY_WAIT_REASON,
        )
        await message.answer(
            f"Выбран ученик: {selected_student.full_name}, "
            f"{selected_student.grade}{selected_student.letter}.\n"
            "Введите причину опоздания (если ее нет, так и запишите) или нажмите 'Отмена'.",
            keyboard=build_vk_late_arrival_reason_keyboard(),
        )

    @bot.on.message(state=States.MORNING_DUTY_WAIT_REASON)
    async def handle_morning_duty_wait_reason(message: Message):
        if message.text and message.text.lower() == ButtonText.CANCEL.lower():
            late_record_draft_by_peer.pop(message.peer_id, None)

            students = student_options_by_peer.get(message.peer_id)

            if students:
                await bot.state_dispenser.set(
                    message.peer_id,
                    States.MORNING_DUTY_CHOOSE_STUDENT,
                )
                await message.answer(
                    "Выберите ученика:",
                    keyboard=build_vk_choose_student_keyboard(students),
                )
                return

            await bot.state_dispenser.set(
                message.peer_id,
                States.MORNING_DUTY_WAIT_SURNAME,
            )
            await message.answer(
                "Введите фамилию опоздавшего.",
                keyboard=build_vk_morning_duty_keyboard(),
            )
            return

        draft = late_record_draft_by_peer.get(message.peer_id)
        morning_duty_session = get_morning_duty_session_for_message(message)

        if draft is None or morning_duty_session is None:
            late_record_draft_by_peer.pop(message.peer_id, None)
            await bot.state_dispenser.set(
                message.peer_id,
                States.MORNING_DUTY_WAIT_SURNAME,
            )
            await message.answer(
                "Не удалось сохранить опоздание. Введите фамилию еще раз.",
                keyboard=build_vk_morning_duty_keyboard(),
            )
            return

        await message.answer("Подождите, опоздание записывается...")

        await save_late_student_record(
            morning_duty_session=morning_duty_session,
            late_student_full_name=draft["late_student_full_name"],
            grade=draft["grade"],
            letter=draft["letter"],
            late_date=date.today(),
            late_time=datetime.now().time(),
            reason=message.text or "",
        )

        student_options_by_peer.pop(message.peer_id, None)
        late_record_draft_by_peer.pop(message.peer_id, None)

        await bot.state_dispenser.set(
            message.peer_id,
            States.MORNING_DUTY_WAIT_SURNAME,
        )
        await message.answer(
            "Опоздание записано. Введите следующую фамилию.",
            keyboard=build_vk_morning_duty_keyboard(),
        )

    # ---- Admin buttons ----
    @bot.on.message(func=text_equals_button(ButtonText.ADMIN_ADD_LATE_CATCHER))
    async def start_add_late_catcher_mode(message: Message):
        if not is_admin(message.from_id, matcher.id_tag):
            await show_main_menu(message)
            return

        await bot.state_dispenser.set(message.peer_id, States.ADMIN_ADD_LATE_CATCHER)
        await message.answer(
            "Введите полное имя пользователя.",
            keyboard=build_vk_admin_cancel_keyboard(),
        )

    @bot.on.message(func=text_equals_button(ButtonText.ADMIN_REMOVE_LATE_CATCHER))
    async def start_remove_late_catcher_mode(message: Message):
        if not is_admin(message.from_id, matcher.id_tag):
            await show_main_menu(message)
            return

        await bot.state_dispenser.set(message.peer_id, States.ADMIN_REMOVE_LATE_CATCHER)
        await message.answer(
            "Внимание! Вы собираетесь удалить пользователя из дежурных по опозданиям! "
            "Введите полное имя пользователя.",
            keyboard=build_vk_admin_cancel_keyboard(),
        )

    @bot.on.message(func=text_equals_button(ButtonText.ADMIN_LIST_LATE_CATCHERS))
    async def show_late_catchers_list(message: Message):
        if not is_admin(message.from_id, matcher.id_tag):
            await show_main_menu(message)
            return

        await message.answer(
            get_late_catchers_list(),
            keyboard=build_vk_admin_keyboard(),
        )

    @bot.on.message(func=text_equals_button(ButtonText.EXIT_ADMIN))
    async def exit_admin_mode(message: Message):
        await delete_state_if_exists(bot, message.peer_id)
        await show_main_menu(message)

    # ---- Fallback for all other messages from registered users ----
    @bot.on.message()
    async def any_other_message(
        message: Message,
    ):  # TODO study this part when you'll be solving register func puzzle
        # Ignore active input states; they are handled above.
        current_state = await bot.state_dispenser.get(message.peer_id)
        if current_state in [
            States.ASK_FULL_NAME,
            States.ADMIN_ADD_LATE_CATCHER,
            States.ADMIN_REMOVE_LATE_CATCHER,
            States.MORNING_DUTY_CHOOSE_BUILDING,
            States.MORNING_DUTY_WAIT_SURNAME,
            States.MORNING_DUTY_CHOOSE_STUDENT,
            States.MORNING_DUTY_WAIT_REASON,
        ]:
            return

        # Send unregistered users to registration.
        if UserRoles.NOT_FOUND in get_user_roles(message.from_id, matcher.id_tag):
            await bot.state_dispenser.set(message.peer_id, States.ASK_FULL_NAME)
            await message.answer(
                "Вы не зарегистрированы. Введите Ваше ФИО в формате: Иванов Иван Иванович"
            )
            return

        # Otherwise, show the main menu.
        await show_main_menu(message)
