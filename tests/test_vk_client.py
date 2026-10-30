import pytest


def test_clean_up_html_symbols(fake_bot_settings):
    from school_routine_bot.vk_bot.vk_client import clean_up_html_symbols

    assert (
        clean_up_html_symbols("<u>underlined</u>, <b>bold</b>, <i>italic</i>")
        == "underlined, bold, italic"
    )


@pytest.mark.parametrize(
    ("message_text", "expected"),
    [
        ("Ваши данные", True),
        ("ваши данные", True),
        ("ВАШИ ДАННЫЕ", True),
        ("Ближайшие дежурства", False),
        (None, False),
    ],
)
def test_text_matches_button_is_case_insensitive(
    message_text, expected, fake_bot_settings
):
    from school_routine_bot.vk_bot.vk_client import text_matches_button

    assert text_matches_button(message_text, "Ваши данные") is expected


class FakeStateDispenser:
    def __init__(self):
        self.peer_ids = set()

    async def delete(self, peer_id):
        if peer_id not in self.peer_ids:
            raise KeyError(peer_id)
        self.peer_ids.remove(peer_id)


class FakeBot:
    def __init__(self):
        self.state_dispenser = FakeStateDispenser()


async def test_delete_state_if_exists_does_not_fail_without_state(
    fake_bot_settings,
):
    from school_routine_bot.vk_bot.vk_client import delete_state_if_exists

    bot = FakeBot()

    await delete_state_if_exists(bot, 123)


async def test_delete_state_if_exists_deletes_existing_state(
    fake_bot_settings,
):
    from school_routine_bot.vk_bot.vk_client import delete_state_if_exists

    bot = FakeBot()
    bot.state_dispenser.peer_ids.add(123)

    await delete_state_if_exists(bot, 123)

    assert 123 not in bot.state_dispenser.peer_ids


@pytest.mark.asyncio
async def test_registration_save_error(mocker, monkeypatch):
    monkeypatch.setenv("morning_duty_table_url", "https://example.com/test-sheet")
    monkeypatch.setenv("vk_bot_token", "fake-vk-token")
    monkeypatch.setenv("bot_token", "123456789:FAKE_TOKEN_FOR_TEST")

    from school_routine_bot.vk_bot import vk_client as client

    handlers = {}

    def register(**kwargs):
        def remember(handler):
            handlers[handler.__name__] = handler
            return handler

        return remember

    bot = FakeBot()
    bot.on = mocker.Mock()
    bot.on.message.side_effect = register
    bot.state_dispenser.peer_ids.add(111)
    client.setup_handlers(bot)

    matcher = mocker.patch.object(client, "matcher")
    matcher.write_full_name_into_user_base.return_value = False
    menu = mocker.patch.object(client, "show_main_menu", new_callable=mocker.AsyncMock)
    message = mocker.Mock(text="Иванов Иван Иванович", from_id=111, peer_id=111)
    message.answer = mocker.AsyncMock()

    await handlers["get_full_name"](message)

    message.answer.assert_awaited_once()
    assert "Не удалось сохранить" in message.answer.await_args.args[0]
    menu.assert_not_awaited()
    assert 111 in bot.state_dispenser.peer_ids
