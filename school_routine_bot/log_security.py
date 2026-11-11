import logging
import traceback


def redact_secrets(text: str, secrets: tuple[str, ...]) -> str:
    """Replace the supplied secrets with a placeholder."""
    for secret in sorted(
        {value for value in secrets if value},
        key=lambda value: len(value),
        reverse=True,
    ):
        text = text.replace(secret, "[REDACTED]")
    return text


class RedactingFormatter(logging.Formatter):
    def __init__(self, secrets: tuple[str, ...], fmt: str | None = None):
        super().__init__(fmt)
        self.secrets = secrets

    def format(self, record: logging.LogRecord) -> str:
        try:
            text = super().format(record)
            return redact_secrets(text, self.secrets)
        except Exception:
            return "Не удалось безопасно подготовить запись лога."


def make_redacting_patcher(secrets: tuple[str, ...]):
    def patch_record(record):
        try:
            text = record["message"]
            exception = record["exception"]

            if exception is not None:
                text += "\n" + "".join(
                    traceback.format_exception(
                        exception.type,
                        exception.value,
                        exception.traceback,
                    )
                )

            safe_text = redact_secrets(text, secrets)
        except Exception:
            safe_text = "Не удалось безопасно подготовить запись лога."

        record["message"] = safe_text
        record["exception"] = None
        record["extra"] = {}

    return patch_record
