from contextlib import contextmanager
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from school_routine_bot.db_files.db_models import Base

_engine = None
_session_maker = None


def create_database(db_url):
    global _engine, _session_maker

    if db_url.startswith("sqlite:///"):
        db_path = Path(db_url.removeprefix("sqlite:///"))
        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info("Redo the directory DATA")
        else:
            logger.info("The directory data already exists")

    _engine = create_engine(db_url)
    _session_maker = sessionmaker(bind=_engine)
    Base.metadata.create_all(_engine)
    return _engine


def get_engine():
    return _engine


@contextmanager
def get_session():
    assert callable(_session_maker)
    session = _session_maker()
    try:
        yield session
    finally:
        session.close()
