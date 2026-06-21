import logging

import resend

import config

log = logging.getLogger(__name__)


class Mailer:
    def send(self, recipient: str, subject: str, body: str) -> None:
        resend.api_key = config.RESEND_API_KEY
        resend.Emails.send({
            "from": config.MAIL_FROM,
            "to": recipient,
            "subject": subject,
            "text": body,
        })
        log.info("Email sent to %s subject=%r", recipient, subject)
