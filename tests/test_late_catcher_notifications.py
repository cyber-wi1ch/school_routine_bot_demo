from unittest.mock import AsyncMock

import pytest

from school_routine_bot.roles import (
    LATE_CATCHER_ADDED_RESULT,
    LATE_CATCHER_REMOVED_RESULT,
    UserMessengerIds,
)


@pytest.mark.parametrize(
    ("result_message", "notification_name"),
    [
        (LATE_CATCHER_ADDED_RESULT, "LATE_CATCHER_ADDED_NOTIFICATION"),
        (LATE_CATCHER_REMOVED_RESULT, "LATE_CATCHER_REMOVED_NOTIFICATION"),
    ],
)
async def test_notify_user_if_late_catcher_role_changed_sends_notification(
    mocker,
    result_message,
    notification_name,
    fake_bot_settings,
):
    from school_routine_bot import late_catcher_notifications as notifications

    expected_notification = getattr(notifications, notification_name)
    messenger_ids = UserMessengerIds(chat_id=123, vk_id=456)
    get_ids_mock = mocker.patch(
        "school_routine_bot.late_catcher_notifications."
        "get_user_messenger_ids_by_full_name",
        return_value=messenger_ids,
    )
    notify_mock = mocker.patch(
        "school_routine_bot.late_catcher_notifications."
        "notify_user_about_late_catcher_role_change",
        new_callable=AsyncMock,
    )

    await notifications.notify_user_if_late_catcher_role_changed(
        result_message,
        "Иванов Иван Иванович",
    )

    get_ids_mock.assert_called_once_with("Иванов Иван Иванович")
    notify_mock.assert_awaited_once_with(messenger_ids, expected_notification)


async def test_notify_user_if_late_catcher_role_changed_ignores_other_results(
    mocker, fake_bot_settings
):
    from school_routine_bot.late_catcher_notifications import (
        notify_user_if_late_catcher_role_changed,
    )

    get_ids_mock = mocker.patch(
        "school_routine_bot.late_catcher_notifications."
        "get_user_messenger_ids_by_full_name",
    )
    notify_mock = mocker.patch(
        "school_routine_bot.late_catcher_notifications."
        "notify_user_about_late_catcher_role_change",
        new_callable=AsyncMock,
    )

    await notify_user_if_late_catcher_role_changed(
        "Пользователь не найден",
        "Иванов Иван Иванович",
    )

    get_ids_mock.assert_not_called()
    notify_mock.assert_not_awaited()
