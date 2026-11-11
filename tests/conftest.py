from pathlib import Path
from typing import Iterator

import pytest
from loguru import logger
from pytest import FixtureRequest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from school_routine_bot.db_files import db_create
from school_routine_bot.db_files.db_models import Base
from school_routine_bot.settings import Settings


@pytest.fixture(autouse=True)
def clean_settings_environment(monkeypatch: pytest.MonkeyPatch):
    for env_var in Settings.model_fields:
        monkeypatch.delenv(env_var, raising=False)


@pytest.fixture(autouse=True)
def use_test_env_file_by_default(
    request: FixtureRequest, monkeypatch: pytest.MonkeyPatch
):
    if "do_not_override_env_file" not in request.keywords:
        monkeypatch.setitem(
            Settings.model_config, "env_file", Path(__file__).parent / "test.env"
        )


@pytest.fixture
def caught_logs() -> Iterator[list[str]]:
    logs: list[str] = []
    handler_id = logger.add(logs.append)
    yield logs
    logger.remove(handler_id)


@pytest.fixture
def engine():
    """Create an in-memory SQLite database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine, mocker):
    """Create a database session for tests."""
    Session = sessionmaker(bind=engine)
    mocker.patch.object(db_create, "_session_maker", Session)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(autouse=True)
def clean_db(engine):
    """Reset the database before each test."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    # Clean up after the test as well
    Base.metadata.drop_all(engine)


@pytest.fixture
def fake_bot_settings(monkeypatch):
    monkeypatch.setenv("morning_duty_table_url", "https://example.com/test-sheet")
    monkeypatch.setenv("vk_bot_token", "fake-vk-token")
    monkeypatch.setenv("bot_token", "123456789:FAKE_TOKEN_FOR_TEST")
