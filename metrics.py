import logging

from prometheus_client import Counter, Gauge, push_to_gateway, REGISTRY

import config

log = logging.getLogger(__name__)

sent_total = Counter(
    "groceror_email_sent_total",
    "Total emails attempted",
    ["status"],
)
processing_errors_total = Counter(
    "groceror_email_processing_errors_total",
    "Total email processing errors",
    ["reason"],
)
consumer_up = Gauge(
    "groceror_email_consumer_up",
    "1 when pika consumer is connected, 0 otherwise",
)


def increment_sent(status: str) -> None:
    sent_total.labels(status=status).inc()
    _push_if_needed()


def increment_error(reason: str) -> None:
    processing_errors_total.labels(reason=reason).inc()
    _push_if_needed()


def set_consumer_status(up: bool) -> None:
    consumer_up.set(1 if up else 0)
    _push_if_needed()


def _push_if_needed() -> None:
    if config.METRICS_BACKEND == "pushgateway":
        try:
            push_to_gateway(config.PUSHGATEWAY_URL, job="groceror-email", registry=REGISTRY)
        except Exception as exc:
            log.warning("Pushgateway push failed: %s", exc)
