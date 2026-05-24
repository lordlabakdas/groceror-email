import smtplib
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from handler import process_message


VALID_RAW = {
    "schema_version": "1.0",
    "event": "send_email",
    "recipient": "user@example.com",
    "subject": "Hello",
    "body": "Test body",
}


@pytest.fixture
def mock_mailer():
    return MagicMock()


def test_valid_message_sends_email(mock_mailer):
    with patch("handler.increment_sent") as mock_sent, \
         patch("handler.increment_error") as mock_err:
        process_message(VALID_RAW, mock_mailer)
    mock_mailer.send.assert_called_once_with(
        "user@example.com", "Hello", "Test body"
    )
    mock_sent.assert_called_once_with("success")
    mock_err.assert_not_called()


def test_unknown_schema_raises_and_increments_error(mock_mailer):
    bad = {**VALID_RAW, "schema_version": "9.9"}
    with patch("handler.increment_error") as mock_err:
        with pytest.raises(ValueError):
            process_message(bad, mock_mailer)
    mock_err.assert_called_once_with("validation")
    mock_mailer.send.assert_not_called()


def test_validation_error_raises_and_increments_error(mock_mailer):
    bad = {**VALID_RAW, "recipient": None}
    with patch("handler.increment_error") as mock_err:
        with pytest.raises((ValidationError, ValueError)):
            process_message(bad, mock_mailer)
    mock_err.assert_called_once_with("validation")
    mock_mailer.send.assert_not_called()


def test_smtp_failure_increments_sent_failure_and_smtp_error(mock_mailer):
    mock_mailer.send.side_effect = smtplib.SMTPException("connection refused")
    with patch("handler.increment_sent") as mock_sent, \
         patch("handler.increment_error") as mock_err:
        with pytest.raises(smtplib.SMTPException):
            process_message(VALID_RAW, mock_mailer)
    mock_sent.assert_called_once_with("failure")
    mock_err.assert_called_once_with("smtp")


def test_os_error_increments_sent_failure_and_smtp_error(mock_mailer):
    mock_mailer.send.side_effect = OSError("connection refused")
    with patch("handler.increment_sent") as mock_sent, \
         patch("handler.increment_error") as mock_err:
        with pytest.raises(OSError):
            process_message(VALID_RAW, mock_mailer)
    mock_sent.assert_called_once_with("failure")
    mock_err.assert_called_once_with("smtp")
