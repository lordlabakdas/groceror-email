import json
import logging
import smtplib

from pydantic import ValidationError

import metrics
from mailer import Mailer
from validator import parse_message

logger = logging.getLogger(__name__)


class EmailEvent:
    @staticmethod
    def send_email(ch, method, properties, body: bytes):
        # --- Deserialise -------------------------------------------------
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON — rejecting without requeue: %s", exc)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            metrics.increment_error("validation")
            return

        # --- Validate ----------------------------------------------------
        try:
            parsed = parse_message(payload)
        except (ValidationError, ValueError) as exc:
            logger.error("Validation error — rejecting without requeue: %s", exc)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            metrics.increment_error("validation")
            return

        # --- Send --------------------------------------------------------
        mailer = Mailer()
        try:
            mailer.send(parsed.recipient, parsed.subject, parsed.body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Sent email to %s subject=%r", parsed.recipient, parsed.subject)
            metrics.increment_sent("success")
        except (smtplib.SMTPException, OSError) as exc:
            requeue = not method.redelivered
            logger.error(
                "SMTP error for recipient=%s: %s — %s",
                parsed.recipient, exc,
                "requeueing" if requeue else "sending to DLQ",
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=requeue)
            metrics.increment_sent("failure")
            metrics.increment_error("smtp")
