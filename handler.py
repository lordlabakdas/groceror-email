import logging
import smtplib

from pydantic import ValidationError

from mailer import Mailer
from metrics import increment_sent, increment_error
from validator import parse_message

log = logging.getLogger(__name__)


def process_message(raw: dict, mailer: Mailer) -> None:
    try:
        parsed = parse_message(raw)
    except (ValidationError, ValueError):
        increment_error("validation")
        raise

    try:
        mailer.send(parsed.recipient, parsed.subject, parsed.body)
    except smtplib.SMTPException:
        increment_sent("failure")
        increment_error("smtp")
        raise

    increment_sent("success")
    log.info("Sent email to %s subject=%r", parsed.recipient, parsed.subject)
