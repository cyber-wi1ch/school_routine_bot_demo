import fcntl
import sqlite3
from contextlib import closing
from pathlib import Path

from loguru import logger


def create_backup(database_path: str | Path):
    # noinspection PyBroadException
    try:
        with open(str(database_path) + "_backup.lock", "a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                logger.info("Бэкап уже выполняется, пропускаем запуск")
                return

            with (
                closing(
                    sqlite3.connect(
                        f"{Path(database_path).resolve().as_uri()}?mode=ro",
                        uri=True,
                    )
                ) as source,
                closing(sqlite3.connect(str(database_path) + "_backup")) as destination,
            ):
                source.backup(destination)

        logger.info("Бэкап успешно сохранен")

    except Exception:
        logger.exception("Не удалось сохранить бэкап SQLite")
