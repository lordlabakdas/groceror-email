import json
import smtplib
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from email_event import EmailEvent

VALID_BODY = json.dumps({
    "schema_version": "1.0",
    "event": "send_email",
    "recipient": "u@example.com",
    "subject": "Hi",
    "body": "Body",
}).encode()


@pytest.fixture
def channel():
    return MagicMock()


@pytest.fixture
def method():
    m = MagicMock()
    m.delivery_tag = 1
    m.redelivered = False
    return m


def test_valid_message_is_acked(channel, method):
    with patch("email_event.Mailer") as MockMailer:
        EmailEvent.send_email(channel, method, MagicMock(), VALID_BODY)
    channel.basic_ack.assert_called_once_with(delivery_tag=1)
    channel.basic_nack.assert_not_called()


def test_valid_message_calls_mailer(channel, method):
    with patch("email_event.Mailer") as MockMailer:
        EmailEvent.send_email(channel, method, MagicMock(), VALID_BODY)
    MockMailer.return_value.send.assert_called_once_with(
        "u@example.com", "Hi", "Body"
    )


def test_invalid_json_nacked_to_dlq(channel, method):
    EmailEvent.send_email(channel, method, MagicMock(), b"not-json")
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)
    channel.basic_ack.assert_not_called()


def test_validation_error_nacked_to_dlq(channel, method):
    bad = json.dumps({"schema_version": "1.0", "event": "send_email"}).encode()
    EmailEvent.send_email(channel, method, MagicMock(), bad)
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)
    channel.basic_ack.assert_not_called()


def test_unknown_schema_nacked_to_dlq(channel, method):
    bad = json.dumps({**json.loads(VALID_BODY), "schema_version": "9.9"}).encode()
    EmailEvent.send_email(channel, method, MagicMock(), bad)
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_first_smtp_failure_requeues(channel, method):
    method.redelivered = False
    with patch("email_event.Mailer") as MockMailer:
        MockMailer.return_value.send.side_effect = smtplib.SMTPException("down")
        EmailEvent.send_email(channel, method, MagicMock(), VALID_BODY)
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=True)


def test_redelivered_smtp_failure_routes_to_dlq(channel, method):
    method.redelivered = True
    with patch("email_event.Mailer") as MockMailer:
        MockMailer.return_value.send.side_effect = smtplib.SMTPException("still down")
        EmailEvent.send_email(channel, method, MagicMock(), VALID_BODY)
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_os_error_first_delivery_requeues(channel, method):
    method.redelivered = False
    with patch("email_event.Mailer") as MockMailer:
        MockMailer.return_value.send.side_effect = OSError("connection refused")
        EmailEvent.send_email(channel, method, MagicMock(), VALID_BODY)
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=True)
