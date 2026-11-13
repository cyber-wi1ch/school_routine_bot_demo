import json

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


@pytest.fixture
def vk_duty(mocker, monkeypatch, fake_bot_settings):
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
    bot.state_dispenser.set = mocker.AsyncMock()
    monkeypatch.setattr(client, "student_options_by_peer", {})
    monkeypatch.setattr(client, "late_record_draft_by_peer", {})
    client.setup_handlers(bot)
    return client, bot, handlers


def make_vk_message(mocker, text, payload=None):
    return mocker.Mock(
        text=text, payload=payload, peer_id=111, from_id=111, answer=mocker.AsyncMock()
    )


LONG_STUDENT_NAME = "Тестов Александр Константин Александрович Младший"


@pytest.mark.parametrize(
    ("full_name", "expected_label"),
    [
        # The ", 5А" suffix adds four characters to the name.
        pytest.param("А" * 34, "А" * 34 + ", 5А", id="38-characters-unchanged"),
        pytest.param("А" * 36, "А" * 36 + ", 5А", id="40-characters-unchanged"),
        pytest.param("А" * 37, "А" * 37 + ", …", id="41-characters-truncated"),
        pytest.param(
            LONG_STUDENT_NAME,
            "Тестов Александр Константин Александров…",
            id="long-name-truncated",
        ),
    ],
)
async def test_vk_student_button_40_symbols_limit_boundaries(
    full_name, expected_label, vk_duty, mocker
):
    from school_routine_bot.pydantic_schemes import StudentFromSheet
    from school_routine_bot.vk_bot.vk_states import States

    client, bot, handlers = vk_duty
    students = [
        StudentFromSheet(full_name=name, grade="5", letter="А")
        for name in ["Тестов Другой Ученик", full_name]
    ]
    client.student_options_by_peer[111] = students
    keyboard = client.build_vk_choose_student_keyboard(students)
    button = json.loads(keyboard.get_json())["buttons"][1][0]["action"]

    assert button["label"] == expected_label

    # VK returns the button payload as a JSON string.
    payload = button.get("payload")
    message = make_vk_message(
        mocker,
        text=button["label"],
        payload=json.dumps(payload) if payload is not None else None,
    )
    await handlers["handle_morning_duty_student_choice"](message)

    message.answer.assert_awaited_once()
    assert full_name in message.answer.await_args.args[0]
    bot.state_dispenser.set.assert_awaited_once_with(
        111, States.MORNING_DUTY_WAIT_REASON
    )
    assert client.late_record_draft_by_peer[111] == {
        "late_student_full_name": full_name,
        "grade": "5",
        "letter": "А",
    }
