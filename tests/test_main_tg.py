import pytest
from telebot.asyncio_helper import RequestTimeout


@pytest.mark.asyncio
async def test_notify_returns_false_on_timeout(mocker, monkeypatch):
    monkeypatch.setenv("morning_duty_table_url", "https://example.com/test-sheet")
    monkeypatch.setenv("vk_bot_token", "fake-vk-token")
    monkeypatch.setenv("bot_token", "123456789:FAKE_TOKEN_FOR_TEST")

    from school_routine_bot import main_tg

    mocker.patch.object(
        main_tg.matcher,
        "get_user_full_name_by_id",
        return_value="Тестовый пользователь",
    )
    send = mocker.patch.object(
        main_tg.bot,
        "send_message",
        new_callable=mocker.AsyncMock,
        side_effect=RequestTimeout("Тестовый таймаут"),
    )

    result = await main_tg.notify(111, "Тест")

    send.assert_awaited_once_with(111, "Тест")
    assert result is False
