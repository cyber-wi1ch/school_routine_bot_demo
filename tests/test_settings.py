import pytest
from pydantic import ValidationError
from pyfakefs.fake_filesystem import FakeFilesystem

from school_routine_bot.settings import get_settings


def get_env_file_content(exclude: str = "") -> str:
    return "\n".join(
        [
            f"{k}={v}"
            for k, v in {
                "table_id": "table_id_test_content",
                "table_url": "https://table_url/test/content",
                "morning_duty_table_url": "https://table_url/test/morning-duty",
                "bot_token": "bot_token_test_content",
                "vk_bot_token": "vk_bot_token_content",
            }.items()
            if k != exclude
        ]
    )


@pytest.mark.do_not_override_env_file
def test_get_settings(fs: FakeFilesystem):
    with pytest.raises(ValidationError):
        get_settings()

    fs.create_file(".env", contents=get_env_file_content())

    settings = get_settings()
    assert settings.bot_token.get_secret_value() == "bot_token_test_content"
    assert settings.table_id == "table_id_test_content"
    assert settings.table_url == "https://table_url/test/content"


@pytest.mark.parametrize(
    "no_valid_secrets_content",
    [
        "",
        "fdfvf",
        "[]",
        "{}",
        get_env_file_content(exclude="bot_token"),
        get_env_file_content(exclude="table_url"),
        get_env_file_content(exclude="morning_duty_table_url"),
        get_env_file_content(exclude="table_id"),
    ],
)
def test_get_settings_with_no_valid_env_file(
    fs: FakeFilesystem, no_valid_secrets_content: str
):
    fs.create_file("test.env", contents=no_valid_secrets_content)

    with pytest.raises(ValidationError):
        get_settings("test.env")
