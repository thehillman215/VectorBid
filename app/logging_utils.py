import logging
import re
from typing import Any

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
NAME_RE = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")


def _scrub(text: str) -> str:
    text = EMAIL_RE.sub("[REDACTED]", text)
    return NAME_RE.sub("[REDACTED]", text)


def install_pii_filter() -> None:
    """Install a global log record factory that redacts PII."""

    old_factory = logging.getLogRecordFactory()

    def factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        if isinstance(record.msg, str):
            record.msg = _scrub(record.msg)
        if record.args:
            record.args = tuple(_scrub(str(a)) for a in record.args)
        return record

    logging.setLogRecordFactory(factory)
