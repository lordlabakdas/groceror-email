import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

log = logging.getLogger(__name__)


class Mailer:
    def send(self, recipient: str, subject: str, body: str) -> None:
        msg = MIMEMultipart()
        msg["From"] = config.MAIL_FROM
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(config.MAIL_SERVER, config.MAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
            smtp.sendmail(config.MAIL_FROM, recipient, msg.as_string())

        log.info("Email sent to %s subject=%r", recipient, subject)
