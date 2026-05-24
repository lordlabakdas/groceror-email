# groceror-email

Microservice that consumes `email_queue` from RabbitMQ and delivers emails via SMTP. Any groceror service can publish `{recipient, subject, body}` to the queue and groceror-email handles delivery.

Published by the [groceror](https://github.com/lordlabakdas/groceror) main service and any companion microservice that imports `client.py`.

---

## Events consumed

| Queue | Trigger |
|---|---|
| `email_queue` | Any service publishes a `send_email` event |

Messages that fail validation are routed to `email_queue.dlq` immediately. SMTP failures are retried once; if redelivery also fails, the message goes to `email_queue.dlq`.

---

## Running alongside groceror

groceror runs as a bare Python process (`make run`) and expects RabbitMQ on `localhost:5672`. groceror-email runs in Docker Compose and connects to that same broker via `host.docker.internal`.

**1. Start RabbitMQ on your host** (if not already running):

```bash
# Linux
sudo systemctl start rabbitmq-server

# or via Docker (standalone)
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

**2. Start groceror:**

```bash
cd /path/to/groceror
make run   # starts on localhost:8000
```

**3. Configure SMTP credentials:**

Create a `.env` file in the project root:

```dotenv
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your@gmail.com
```

For Gmail, generate an [App Password](https://myaccount.google.com/apppasswords) (requires 2FA enabled).

**4. Start groceror-email:**

```bash
docker compose up --build
```

**Verify it's working:**

```bash
# metric counter present
curl -s localhost:8003/metrics | grep groceror_email
```

Open Grafana at http://localhost:3003 (admin / admin) — the **Email Events** dashboard shows delivery rate, total sent, error rate, and consumer status in real time.

> **Note:** If RabbitMQ refuses the connection with a 403 auth error, see the [authentication fix](#rabbitmq-authentication) section below.

---

## Sending an email from another service

Import `EmailClient` from `client.py` in any groceror service:

```python
from client import EmailClient

EmailClient().send(
    recipient="user@example.com",
    subject="Welcome to groceror",
    body="Hello, your account is ready.",
)
```

`EmailClient.send()` opens a fresh connection, publishes the message to `email_queue`, and returns. Delivery is asynchronous.

---

## Running with Docker Compose

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| groceror-email API | http://localhost:8003 |
| Prometheus | http://localhost:9092 |
| Grafana | http://localhost:3003 (admin / admin) |

The **Email Events** Grafana dashboard is provisioned automatically on startup.

---

## Running locally (without Docker)

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # for tests only

python main.py
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `RABBITMQ_HOST` | `localhost` | RabbitMQ broker hostname |
| `RABBITMQ_PORT` | `5672` | RabbitMQ broker port |
| `RABBITMQ_USER` | `guest` | RabbitMQ username |
| `RABBITMQ_PASS` | `guest` | RabbitMQ password |
| `RABBITMQ_VHOST` | `/` | RabbitMQ virtual host |
| `MAIL_SERVER` | `smtp.gmail.com` | SMTP server hostname |
| `MAIL_PORT` | `587` | SMTP port (STARTTLS) |
| `MAIL_USERNAME` | _(empty)_ | SMTP login username |
| `MAIL_PASSWORD` | _(empty)_ | SMTP login password or app password |
| `MAIL_FROM` | _(MAIL_USERNAME)_ | Sender address in the From header |
| `API_HOST` | `0.0.0.0` | FastAPI bind address |
| `API_PORT` | `8003` | FastAPI port |
| `METRICS_BACKEND` | `prometheus` | `prometheus` (container) or `pushgateway` (Lambda) |
| `PUSHGATEWAY_URL` | _(empty)_ | Pushgateway URL, required when `METRICS_BACKEND=pushgateway` |

### Using a `.env` file

```dotenv
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your@gmail.com
RABBITMQ_USER=groceror
RABBITMQ_PASS=changeme
```

---

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Returns `{"status": "ok"}` |
| `GET /metrics` | Prometheus metrics (text/plain) |

---

## Metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `groceror_email_sent_total` | Counter | `status` (`success`/`failure`) | Emails attempted |
| `groceror_email_processing_errors_total` | Counter | `reason` (`validation`/`smtp`) | Validation or delivery errors |
| `groceror_email_consumer_up` | Gauge | — | `1` when connected to RabbitMQ, `0` otherwise |

---

## Message contract

groceror-email expects messages in this envelope format:

```json
{
  "schema_version": "1.0",
  "event": "send_email",
  "recipient": "user@example.com",
  "subject": "Welcome to groceror",
  "body": "Plain text email body"
}
```

Use `EmailClient` from `client.py` to build and publish this envelope correctly.

---

## Error handling

| Failure | Behaviour |
|---|---|
| RabbitMQ unreachable at startup | Reconnect loop with 5s backoff |
| Invalid JSON | NACK `requeue=False` → DLQ |
| Pydantic or schema validation failure | NACK `requeue=False` → DLQ |
| SMTP/network failure, first delivery | NACK `requeue=True` — retry once |
| SMTP/network failure, redelivered | NACK `requeue=False` → DLQ |

---

## RabbitMQ authentication

By default, RabbitMQ's `guest` user only accepts connections from `localhost`. Since groceror-email runs inside Docker, it connects from a different IP and will get a 403 refused error.

**Fix — allow guest from remote hosts (dev only):**

```bash
# Linux
echo "loopback_users = none" | sudo tee -a /etc/rabbitmq/rabbitmq.conf
sudo systemctl restart rabbitmq-server
```

Then restart the stack: `docker compose restart groceror-email`

---

## AWS Lambda

`lambda_handler.py` supports both Amazon MQ and SQS triggers. Point your Lambda trigger at `lambda_handler.handler`.

Set `METRICS_BACKEND=pushgateway` and configure `PUSHGATEWAY_URL` to push metrics from Lambda invocations.

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```
