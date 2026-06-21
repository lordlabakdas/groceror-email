import base64
import json
import logging

from mailer import Mailer
from validator import parse_message

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_mailer: Mailer | None = None


def _get_mailer() -> Mailer:
    global _mailer
    if _mailer is None:
        _mailer = Mailer()
    return _mailer


def handler(event: dict, context) -> dict:
    """AWS Lambda entry point for Amazon MQ and SQS triggers.

    Amazon MQ event keys:  event["rmqMessagesByQueue"][queue_key][*]["data"] (base64)
    SQS event keys:        event["Records"][*]["body"] (JSON string)
    """
    mailer = _get_mailer()
    failed = 0
    total = 0

    if "rmqMessagesByQueue" in event:
        for messages in event["rmqMessagesByQueue"].values():
            for msg in messages:
                total += 1
                try:
                    raw = json.loads(base64.b64decode(msg["data"]).decode("utf-8"))
                    parsed = parse_message(raw)
                    mailer.send(parsed.recipient, parsed.subject, parsed.body)
                except Exception as exc:
                    log.error("Failed to process Amazon MQ message: %s", exc)
                    failed += 1

    elif "Records" in event:
        total = len(event["Records"])
        for record in event["Records"]:
            try:
                raw = json.loads(record["body"])
                parsed = parse_message(raw)
                mailer.send(parsed.recipient, parsed.subject, parsed.body)
            except Exception as exc:
                log.error("Failed to process SQS record: %s", exc)
                failed += 1

    return {"processed": total - failed, "failed": failed}
