import smtplib
from unittest.mock import patch, MagicMock

import pytest

from mailer import Mailer


def test_send_connects_to_configured_smtp_server():
    with patch("mailer.smtplib.SMTP") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        mailer = Mailer()
        mailer.send("to@example.com", "Subject", "Body")

        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once()
        mock_smtp.sendmail.assert_called_once()


def test_send_raises_on_smtp_error():
    with patch("mailer.smtplib.SMTP") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp.sendmail.side_effect = smtplib.SMTPException("send failed")
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        mailer = Mailer()
        with pytest.raises(smtplib.SMTPException):
            mailer.send("to@example.com", "Subject", "Body")


def test_send_uses_correct_recipient():
    with patch("mailer.smtplib.SMTP") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        mailer = Mailer()
        mailer.send("recipient@example.com", "Subject", "Body")

        call_args = mock_smtp.sendmail.call_args
        assert "recipient@example.com" in call_args[0][1]
