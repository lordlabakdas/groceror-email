import json
import logging

import pika

import config

log = logging.getLogger(__name__)


class EmailClient:
    def send(self, recipient: str, subject: str, body: str) -> None:
        message = {
            "schema_version": "1.0",
            "event": "send_email",
            "recipient": recipient,
            "subject": subject,
            "body": body,
        }
        credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASS)
        params = pika.ConnectionParameters(
            host=config.RABBITMQ_HOST,
            port=config.RABBITMQ_PORT,
            virtual_host=config.RABBITMQ_VHOST,
            credentials=credentials,
        )
        connection = pika.BlockingConnection(params)
        try:
            channel = connection.channel()
            channel.queue_declare(queue=config.QUEUE_NAME, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=config.QUEUE_NAME,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                ),
            )
            log.info("Queued email to %s subject=%r", recipient, subject)
        finally:
            connection.close()
