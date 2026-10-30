import pytest


@pytest.mark.asyncio
async def test_registration_save_error(mocker, fake_bot_settings):
    from school_routine_bot import tg_client as client

    matcher = mocker.patch.object(client, "matcher")
    matcher.write_full_name_into_user_base.return_value = False
    send = mocker.patch.object(
        client.bot, "send_message", new_callable=mocker.AsyncMock
    )
    menu = mocker.patch.object(
        client, "show_buttons_bar", new_callable=mocker.AsyncMock
    )
    mocker.patch.object(client, "users_states", {111: client.STATE_ASK_FULL_NAME})
    message = mocker.Mock(text="Иванов Иван Иванович", chat=mocker.Mock(id=111))

    await client.get_full_name(message)

    send.assert_awaited_once()
    assert "Не удалось сохранить" in send.await_args.args[1]
    menu.assert_not_awaited()
    assert client.users_states[111] == client.STATE_ASK_FULL_NAME
