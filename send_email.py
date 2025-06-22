import pika
import json
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class EmailClient:
    def __init__(self):
        self.credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER", "guest"), os.getenv("RABBITMQ_PASS", "guest")
        )
        self.parameters = pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            credentials=self.credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        self.queue_name = "email_queue"

    def _get_connection(self) -> pika.BlockingConnection:
        """Get a new RabbitMQ connection"""
        return pika.BlockingConnection(self.parameters)

    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """
        Send an email request to the email service

        Args:
            recipient: Email address of the recipient
            subject: Email subject
            body: Email body

        Returns:
            bool: True if the request was successfully queued, False otherwise
        """
        try:
            connection = self._get_connection()
            channel = connection.channel()

            # Ensure queue exists
            channel.queue_declare(queue=self.queue_name, durable=True)

            # Prepare message
            message = {"recipient": recipient, "subject": subject, "body": body}

            # Publish message
            channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                ),
            )

            logger.info(f"Email request queued for {recipient}")
            connection.close()
            return True

        except Exception as e:
            logger.error(f"Failed to queue email request: {str(e)}")
            return False
