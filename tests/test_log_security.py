import logging
import subprocess
import sys
from pathlib import Path

import pytest

from school_routine_bot import log_security
from school_routine_bot.log_security import redact_secrets


def test_redacts_both_tokens():
    text = "Ошибка: bot=FAKE_TG_TOKEN access_token=FAKE_VK_TOKEN"

    result = redact_secrets(
        text,
        ("FAKE_TG_TOKEN", "FAKE_VK_TOKEN"),
    )

    assert result == "Ошибка: bot=[REDACTED] access_token=[REDACTED]"


def test_empty_secret_does_not_change_text():
    assert redact_secrets("Обычное сообщение", ("",)) == "Обычное сообщение"


def test_longer_secret_is_replaced_first():
    assert (
        redact_secrets(
            "FAKE_TOKEN_LONG",
            ("FAKE_TOKEN", "FAKE_TOKEN_LONG"),
        )
        == "[REDACTED]"
    )


def test_setup_logger_masks_exception_in_console_and_file(tmp_path):
    project_root = Path(__file__).resolve().parents[1]

    script = """
import sys

sys.path.insert(0, sys.argv[1])

from loguru import logger
from school_routine_bot.setup_logging import setup_logger

setup_logger(secrets=("FAKE_TG_TOKEN", "FAKE_VK_TOKEN"))
logger.info("Обычная запись: token=FAKE_TG_TOKEN")

try:
    try:
        raise ValueError("Ошибка запроса: token=FAKE_TG_TOKEN")
    except ValueError as cause:
        raise RuntimeError(
            "Не удалось отправить: access_token=FAKE_VK_TOKEN"
        ) from cause
except RuntimeError:
    logger.exception("Проверка маскирования")

logger.remove()
"""

    result = subprocess.run(
        [sys.executable, "-B", "-c", script, str(project_root)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )

    assert result.returncode == 0, result.stderr

    file_text = (tmp_path / "school_routine_bot.log").read_text(encoding="utf-8")

    for output in (result.stderr, file_text):
        assert "FAKE_TG_TOKEN" not in output
        assert "FAKE_VK_TOKEN" not in output
        assert "[REDACTED]" in output
        assert "Проверка маскирования" in output
        assert "RuntimeError" in output
        assert "Traceback" in output
        assert "ValueError" in output
        assert "Обычная запись: token=[REDACTED]" in output


def test_setup_logger_masks_telegram_exception(tmp_path):
    project_root = Path(__file__).resolve().parents[1]

    script = """
import sys

sys.path.insert(0, sys.argv[1])

import telebot
from school_routine_bot.setup_logging import setup_logger

assert telebot.logger.handlers, "Нет обработчиков Telegram"

setup_logger(secrets=("FAKE_TG_TOKEN", "FAKE_VK_TOKEN"))

try:
    raise RuntimeError(
        "Request failed: /botFAKE_TG_TOKEN/sendMessage"
        "?access_token=FAKE_VK_TOKEN"
    )
except RuntimeError:
    telebot.logger.exception("Проверка Telegram")
"""

    result = subprocess.run(
        [sys.executable, "-B", "-c", script, str(project_root)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )

    assert result.returncode == 0, result.stderr

    output = result.stderr
    assert "FAKE_TG_TOKEN" not in output
    assert "FAKE_VK_TOKEN" not in output
    assert "[REDACTED]" in output
    assert "Проверка Telegram" in output
    assert "RuntimeError" in output
    assert "Traceback" in output


@pytest.mark.parametrize("target", ["loguru", "telegram"])
def test_redaction_failure_returns_safe_message(monkeypatch, target):
    secret = "FAKE_SECRET"

    def broken_redaction(*args, **kwargs):
        raise RuntimeError("Сбой очистки: " + secret)

    monkeypatch.setattr(
        log_security,
        "redact_secrets",
        broken_redaction,
    )

    if target == "loguru":
        record = {
            "message": "Токен: " + secret,
            "exception": None,
        }
        patcher = log_security.make_redacting_patcher((secret,))
        patcher(record)
        result = record["message"]
        assert record["exception"] is None
    else:
        record = logging.makeLogRecord(
            {
                "msg": "Токен: " + secret,
                "args": (),
            }
        )
        formatter = log_security.RedactingFormatter((secret,))
        result = formatter.format(record)

    assert result == "Не удалось безопасно подготовить запись лога."
    assert secret not in result


@pytest.mark.parametrize(
    ("use_keyword", "disk_full"),
    [(True, False), (False, True), (True, True)],
    ids=["keyword-normal-write", "message-disk-full", "keyword-disk-full"],
)
def test_loguru_does_not_leak_token_on_file_write_failure(
    tmp_path, use_keyword, disk_full
):
    """Очищаться должен и аварийный вывод, а не только обычное сообщение."""
    project_root = Path(__file__).resolve().parents[1]
    script = """
import errno
import sys
from contextlib import nullcontext
from unittest.mock import patch

sys.path.insert(0, sys.argv[1])

from loguru import logger
from loguru._file_sink import FileSink
from school_routine_bot.setup_logging import setup_logger

secret = "FAKE_TOKEN_FOR_DISK_FAILURE_CHECK"
use_keyword = sys.argv[2] == "1"
disk_full = sys.argv[3] == "1"
setup_logger(secrets=(secret,))

# Подменяется только запись файла: форматирование и диагностика — настоящие.
failure = (
    patch.object(
        FileSink,
        "write",
        side_effect=OSError(errno.ENOSPC, "No space left on device"),
    )
    if disk_full else nullcontext()
)
try:
    with failure as writer:
        if use_keyword:
            logger.info("Request token={token}", token=secret)
        else:
            logger.info("Request token=" + secret)
        if disk_full:
            assert writer.called, "File-write failure was not exercised"
finally:
    logger.remove()
"""
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            script,
            str(project_root),
            str(int(use_keyword)),
            str(int(disk_full)),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert "Request token=[REDACTED]" in result.stderr
    file_text = (tmp_path / "school_routine_bot.log").read_text(encoding="utf-8")
    for output in (result.stdout, result.stderr, file_text):
        assert "FAKE_TOKEN_FOR_DISK_FAILURE_CHECK" not in output
