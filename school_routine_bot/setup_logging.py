import logging
import sys

from loguru import logger

from school_routine_bot.log_security import (
    RedactingFormatter,
    make_redacting_patcher,
)


def setup_logger(secrets: tuple[str, ...]):
    logging.raiseExceptions = False
    logger.remove()
    logger.configure(patcher=make_redacting_patcher(secrets))
    logger.add(sys.stderr, level="INFO", diagnose=False)
    logger.add(
        "school_routine_bot.log",
        level="INFO",
        colorize=False,
        rotation="10 MB",
        retention=10,
        diagnose=False,
    )

    telegram_logger = logging.getLogger("TeleBot")

    for handler in telegram_logger.handlers:
        handler.setFormatter(
            RedactingFormatter(
                secrets,
                fmt="%(asctime)s | %(levelname)s | %(name)s - %(message)s",
            )
        )

    telegram_logger.propagate = False
