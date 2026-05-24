import os

RABBITMQ_HOST   = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT   = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER   = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS   = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_VHOST  = os.getenv("RABBITMQ_VHOST", "/")

MAIL_SERVER   = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT     = int(os.getenv("MAIL_PORT", 587))
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM     = os.getenv("MAIL_FROM", MAIL_USERNAME)

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8003))

METRICS_BACKEND = os.getenv("METRICS_BACKEND", "prometheus")
PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "")

QUEUE_NAME   = "email_queue"
DLQ_NAME     = "email_queue.dlq"
DLX_EXCHANGE = "dlx"
