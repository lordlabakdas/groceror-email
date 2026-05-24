import json
from unittest.mock import MagicMock, patch

from client import EmailClient


def test_send_publishes_correct_envelope():
    with patch("client.pika.BlockingConnection") as mock_conn_cls:
        mock_channel = MagicMock()
        mock_conn_cls.return_value.channel.return_value = mock_channel

        EmailClient().send(
            recipient="r@example.com",
            subject="Hello",
            body="World",
        )

    mock_channel.basic_publish.assert_called_once()
    body = json.loads(mock_channel.basic_publish.call_args.kwargs["body"])
    assert body["event"] == "send_email"
    assert body["schema_version"] == "1.0"
    assert body["recipient"] == "r@example.com"
    assert body["subject"] == "Hello"
    assert body["body"] == "World"


def test_send_publishes_to_email_queue():
    with patch("client.pika.BlockingConnection") as mock_conn_cls:
        mock_channel = MagicMock()
        mock_conn_cls.return_value.channel.return_value = mock_channel

        EmailClient().send("r@example.com", "S", "B")

    assert mock_channel.basic_publish.call_args.kwargs["routing_key"] == "email_queue"
