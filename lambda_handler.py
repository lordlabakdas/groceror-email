import base64
import json
import logging

from handler import process_message
from mailer import Mailer

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_mailer: Mailer | None = None


def _get_mailer() -> Mailer:
    global _mailer
    if _mailer is None:
        _mailer = Mailer()
    return _mailer


def handler(event: dict, context) -> dict:
    mailer = _get_mailer()
    failed = 0
    total = 0

    if "rmqMessagesByQueue" in event:
        for messages in event["rmqMessagesByQueue"].values():
            for msg in messages:
                total += 1
                try:
                    body = base64.b64decode(msg["data"]).decode("utf-8")
                    process_message(json.loads(body), mailer)
                except Exception as exc:
                    log.error("Failed to process Amazon MQ message: %s", exc)
                    failed += 1

    elif "Records" in event:
        total = len(event["Records"])
        for record in event["Records"]:
            try:
                process_message(json.loads(record["body"]), mailer)
            except Exception as exc:
                log.error("Failed to process SQS record: %s", exc)
                failed += 1

    return {"processed": total - failed, "failed": failed}
