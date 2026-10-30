import random

from loguru import logger
from telebot.async_telebot import AsyncTeleBot
from vkbottle import API

from school_routine_bot.bot_keyboards import (
    build_tg_main_keyboard,
    build_vk_main_keyboard,
)
from school_routine_bot.roles import (
    LATE_CATCHER_ADDED_RESULT,
    LATE_CATCHER_REMOVED_RESULT,
    UserMessengerIds,
    get_user_messenger_ids_by_full_name,
)
from school_routine_bot.settings import get_settings

settings = get_settings()

tg_bot = AsyncTeleBot(settings.bot_token.get_secret_value())
vk_api = API(token=settings.vk_bot_token.get_secret_value())

LATE_CATCHER_ADDED_NOTIFICATION = (
    "Вы добавлены в дежурные по опозданиям. Теперь Вам доступна новая кнопка"
)
LATE_CATCHER_REMOVED_NOTIFICATION = "Вы больше не дежурный по опозданиям"


async def notify_user_if_late_catcher_role_changed(
    result_message: str,
    full_name: str,
):
    notification_text_by_result = {
        LATE_CATCHER_ADDED_RESULT: LATE_CATCHER_ADDED_NOTIFICATION,
        LATE_CATCHER_REMOVED_RESULT: LATE_CATCHER_REMOVED_NOTIFICATION,
    }
    notification_text = notification_text_by_result.get(result_message)

    if notification_text is None:
        return

    await notify_user_about_late_catcher_role_change(
        get_user_messenger_ids_by_full_name(full_name),
        notification_text,
    )


async def notify_user_about_late_catcher_role_change(
    messenger_ids: UserMessengerIds | None,
    notification_text: str,
):
    if messenger_ids is None:
        logger.warning(
            "Could not notify user about late_catcher role change: user not found"
        )
        return

    if messenger_ids.chat_id is None and messenger_ids.vk_id is None:
        logger.warning(
            "Could not notify user about late_catcher role change: "
            "messenger ids not found"
        )
        return

    if messenger_ids.chat_id is not None:
        await notify_tg_user_about_late_catcher_role_change(
            messenger_ids.chat_id,
            notification_text,
        )

    if messenger_ids.vk_id is not None:
        await notify_vk_user_about_late_catcher_role_change(
            messenger_ids.vk_id,
            notification_text,
        )


async def notify_tg_user_about_late_catcher_role_change(
    chat_id: int,
    notification_text: str,
):
    try:
        await tg_bot.send_message(
            chat_id,
            notification_text,
            reply_markup=build_tg_main_keyboard(chat_id),
        )
    except Exception as e:
        logger.warning(
            f"Could not notify TG user {chat_id} about late_catcher role change: {e}"
        )


async def notify_vk_user_about_late_catcher_role_change(
    user_id: int,
    notification_text: str,
):
    try:
        await vk_api.messages.send(
            user_id=user_id,
            message=notification_text,
            keyboard=build_vk_main_keyboard(user_id).get_json(),
            random_id=random.randint(1, 2**31),
            dont_parse_links=None,
        )
    except Exception as e:
        logger.warning(
            f"Could not notify VK user {user_id} about late_catcher role change: {e}"
        )
