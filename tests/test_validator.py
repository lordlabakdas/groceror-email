import pytest
from pydantic import ValidationError

from validator import parse_message, EmailMessage


VALID = {
    "schema_version": "1.0",
    "event": "send_email",
    "recipient": "user@example.com",
    "subject": "Hello",
    "body": "Test body",
}


def test_parse_valid_message():
    msg = parse_message(VALID)
    assert isinstance(msg, EmailMessage)
    assert msg.recipient == "user@example.com"
    assert msg.subject == "Hello"
    assert msg.body == "Test body"


def test_unknown_schema_version_raises():
    bad = {**VALID, "schema_version": "9.9"}
    with pytest.raises(ValueError, match="schema_version"):
        parse_message(bad)


def test_unknown_event_raises():
    bad = {**VALID, "event": "not_send_email"}
    with pytest.raises(ValueError, match="event"):
        parse_message(bad)


def test_missing_recipient_raises():
    bad = {k: v for k, v in VALID.items() if k != "recipient"}
    with pytest.raises(ValidationError):
        parse_message(bad)


def test_missing_subject_raises():
    bad = {k: v for k, v in VALID.items() if k != "subject"}
    with pytest.raises(ValidationError):
        parse_message(bad)


def test_missing_body_raises():
    bad = {k: v for k, v in VALID.items() if k != "body"}
    with pytest.raises(ValidationError):
        parse_message(bad)
