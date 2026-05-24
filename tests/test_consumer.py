import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from consumer import _on_message, _declare_topology


def _make_validation_error() -> ValidationError:
    class _M(BaseModel):
        x: int
    try:
        _M(x="not-an-int")
    except ValidationError as exc:
        return exc
    raise AssertionError("Expected ValidationError")


@pytest.fixture
def channel():
    return MagicMock()


@pytest.fixture
def method():
    m = MagicMock()
    m.delivery_tag = 1
    m.redelivered = False
    return m


@pytest.fixture
def mock_mailer():
    return MagicMock()


VALID_BODY = json.dumps({
    "schema_version": "1.0",
    "event": "send_email",
    "recipient": "u@example.com",
    "subject": "Hi",
    "body": "Body",
}).encode()


def test_valid_message_is_acked(channel, method, mock_mailer):
    with patch("consumer.process_message"):
        _on_message(channel, method, MagicMock(), VALID_BODY, mock_mailer)
    channel.basic_ack.assert_called_once_with(delivery_tag=1)
    channel.basic_nack.assert_not_called()


def test_invalid_json_routes_to_dlq(channel, method, mock_mailer):
    _on_message(channel, method, MagicMock(), b"not-json", mock_mailer)
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)
    channel.basic_ack.assert_not_called()


def test_validation_error_routes_to_dlq_on_first_delivery(channel, method, mock_mailer):
    method.redelivered = False
    with patch("consumer.process_message", side_effect=_make_validation_error()):
        _on_message(channel, method, MagicMock(), VALID_BODY, mock_mailer)
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_value_error_routes_to_dlq_on_first_delivery(channel, method, mock_mailer):
    method.redelivered = False
    with patch("consumer.process_message", side_effect=ValueError("bad schema")):
        _on_message(channel, method, MagicMock(), VALID_BODY, mock_mailer)
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_smtp_failure_first_delivery_requeues(channel, method, mock_mailer):
    method.redelivered = False
    with patch("consumer.process_message", side_effect=Exception("smtp down")):
        _on_message(channel, method, MagicMock(), VALID_BODY, mock_mailer)
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=True)


def test_smtp_failure_redelivered_routes_to_dlq(channel, method, mock_mailer):
    method.redelivered = True
    with patch("consumer.process_message", side_effect=Exception("still down")):
        _on_message(channel, method, MagicMock(), VALID_BODY, mock_mailer)
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_declare_topology_creates_email_queue_and_dlq(channel):
    _declare_topology(channel)
    queue_names = [
        c.args[0] if c.args else c.kwargs.get("queue")
        for c in channel.queue_declare.call_args_list
    ]
    assert "email_queue" in queue_names
    assert "email_queue.dlq" in queue_names
