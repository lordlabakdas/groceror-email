from unittest.mock import patch, MagicMock

import metrics


def test_increment_sent_success_calls_counter():
    with patch.object(metrics.sent_total, "labels") as mock_labels:
        mock_inc = MagicMock()
        mock_labels.return_value.inc = mock_inc
        metrics.increment_sent("success")
    mock_labels.assert_called_once_with(status="success")
    mock_inc.assert_called_once()


def test_increment_sent_failure_calls_counter():
    with patch.object(metrics.sent_total, "labels") as mock_labels:
        mock_inc = MagicMock()
        mock_labels.return_value.inc = mock_inc
        metrics.increment_sent("failure")
    mock_labels.assert_called_once_with(status="failure")
    mock_inc.assert_called_once()


def test_increment_error_calls_counter():
    with patch.object(metrics.processing_errors_total, "labels") as mock_labels:
        mock_inc = MagicMock()
        mock_labels.return_value.inc = mock_inc
        metrics.increment_error("smtp")
    mock_labels.assert_called_once_with(reason="smtp")
    mock_inc.assert_called_once()


def test_set_consumer_status_up():
    with patch.object(metrics.consumer_up, "set") as mock_set:
        metrics.set_consumer_status(True)
    mock_set.assert_called_once_with(1)


def test_set_consumer_status_down():
    with patch.object(metrics.consumer_up, "set") as mock_set:
        metrics.set_consumer_status(False)
    mock_set.assert_called_once_with(0)


def test_pushgateway_not_called_for_prometheus_backend():
    import config
    original = config.METRICS_BACKEND
    config.METRICS_BACKEND = "prometheus"
    try:
        with patch("metrics.push_to_gateway") as mock_push:
            metrics.increment_sent("success")
        mock_push.assert_not_called()
    finally:
        config.METRICS_BACKEND = original


def test_pushgateway_called_when_backend_is_pushgateway():
    import config
    original = config.METRICS_BACKEND
    config.METRICS_BACKEND = "pushgateway"
    try:
        with patch("metrics.push_to_gateway") as mock_push:
            metrics.increment_sent("success")
        mock_push.assert_called_once()
    finally:
        config.METRICS_BACKEND = original


def test_pushgateway_exception_does_not_raise():
    import config
    original = config.METRICS_BACKEND
    config.METRICS_BACKEND = "pushgateway"
    try:
        with patch("metrics.push_to_gateway", side_effect=Exception("connection failed")):
            metrics.increment_sent("success")  # must not raise
    finally:
        config.METRICS_BACKEND = original
