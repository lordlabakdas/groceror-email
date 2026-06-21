import base64
import json
from unittest.mock import patch, MagicMock

import lambda_handler as lh

VALID_RAW = {
    "schema_version": "1.0",
    "event": "send_email",
    "recipient": "u@example.com",
    "subject": "Hi",
    "body": "Body",
}


def _amq_event(raw: dict) -> dict:
    encoded = base64.b64encode(json.dumps(raw).encode()).decode()
    return {
        "rmqMessagesByQueue": {
            "email_queue::/": [{"data": encoded, "redelivered": False}]
        }
    }


def _sqs_event(raw: dict) -> dict:
    return {"Records": [{"body": json.dumps(raw), "messageId": "msg-1"}]}


def test_amazon_mq_event_sends_email():
    mock_mailer = MagicMock()
    with patch("lambda_handler._get_mailer", return_value=mock_mailer):
        result = lh.handler(_amq_event(VALID_RAW), None)
    mock_mailer.send.assert_called_once_with("u@example.com", "Hi", "Body")
    assert result["failed"] == 0


def test_sqs_event_sends_email():
    mock_mailer = MagicMock()
    with patch("lambda_handler._get_mailer", return_value=mock_mailer):
        result = lh.handler(_sqs_event(VALID_RAW), None)
    mock_mailer.send.assert_called_once_with("u@example.com", "Hi", "Body")
    assert result["failed"] == 0


def test_send_failure_increments_failed_count():
    mock_mailer = MagicMock()
    mock_mailer.send.side_effect = Exception("smtp down")
    with patch("lambda_handler._get_mailer", return_value=mock_mailer):
        result = lh.handler(_sqs_event(VALID_RAW), None)
    assert result["failed"] == 1


def test_invalid_schema_increments_failed_count():
    mock_mailer = MagicMock()
    bad = {**VALID_RAW, "schema_version": "9.9"}
    with patch("lambda_handler._get_mailer", return_value=mock_mailer):
        result = lh.handler(_sqs_event(bad), None)
    assert result["failed"] == 1
    mock_mailer.send.assert_not_called()
