import pytest


@pytest.mark.asyncio
async def test_notify_returns_false_on_send_error(mocker, monkeypatch):
    monkeypatch.setenv("morning_duty_table_url", "https://example.com/test-sheet")
    monkeypatch.setenv("vk_bot_token", "fake-vk-token")
    monkeypatch.setenv("bot_token", "123456789:FAKE_TOKEN_FOR_TEST")

    from school_routine_bot.vk_bot import main_vk

    mocker.patch.object(
        main_vk.matcher,
        "get_user_full_name_by_id",
        return_value="Тестовый пользователь",
    )
    api = mocker.patch.object(main_vk, "vk_api")
    send = mocker.AsyncMock(
        side_effect=TimeoutError("Тестовый таймаут"),
    )
    api.messages.send = send

    result = await main_vk.notify(111, "Тест")

    send.assert_awaited_once_with(
        user_id=111,
        message="Тест",
        random_id=mocker.ANY,
        dont_parse_links=None,
    )
    assert result is False
