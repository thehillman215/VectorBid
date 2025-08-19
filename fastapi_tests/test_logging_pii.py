import logging

from app.main import app  # noqa: F401 - ensure filter is installed


def test_log_filter_redacts_pii(caplog):
    logger = logging.getLogger("pii_test")
    with caplog.at_level(logging.INFO):
        logger.info("User John Doe john.doe@example.com accessed")
    assert "John Doe" not in caplog.text
    assert "john.doe@example.com" not in caplog.text
    assert "[REDACTED]" in caplog.text
