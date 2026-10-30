from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    table_id: str
    table_url: str
    morning_duty_table_url: str
    bot_token: SecretStr
    vk_bot_token: SecretStr
    messenger_tag: Literal["vk", "tg"] = "tg"

    ###
    # здесь мы указываем путь к файлу бд, с которым будем работать.
    database: str = (
        f"sqlite:///{(Path(__file__).parent / '../data/bot_db.sqlite').absolute()}"
    )

    # user_base_file: Path = Path(__file__).parent / "../user_base.json" ->
    # TODO When delete - make sure the very file is deleted
    credentials_for_tables_file: Path = (
        Path(__file__).parent / "../credentials_for_tables.json"
    )

    model_config = SettingsConfigDict(
        env_file=(".env", Path(__file__).parent / "../.env"),
        extra="ignore",
        hide_input_in_errors=True,
    )

    admins: list[int] = []  # TODO move the info into db


class SettingsToAccessGoogleSheets(BaseSettings):
    table_id: str
    credentials_for_tables_file: Path = (
        Path(__file__).parent / "../credentials_for_tables.json"
    )

    model_config = SettingsConfigDict(
        env_file=(".env", Path(__file__).parent / "../.env"),
        extra="ignore",
        hide_input_in_errors=True,
    )


def get_settings(env_file: str | None = None) -> Settings:
    return Settings(**{"_env_file": env_file} if env_file else {})
