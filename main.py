from flask import Flask
from flask_mail import Mail, Message
import pika
import json
import os
from dotenv import load_dotenv
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Flask-Mail
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False

mail = Mail(app)


def setup_rabbit_connection():
    """Establish connection to RabbitMQ"""
    try:
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER", "guest"), os.getenv("RABBITMQ_PASS", "guest")
        )
        parameters = pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        return pika.BlockingConnection(parameters)
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
        raise


def send_email(recipient, subject, body):
    """Send email using Flask-Mail"""
    try:
        msg = Message(
            subject, sender=app.config["MAIL_USERNAME"], recipients=[recipient]
        )
        msg.body = body
        mail.send(msg)
        logger.info(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False


def process_email_request(ch, method, properties, body):
    """Process incoming email requests from the queue"""
    try:
        data = json.loads(body)
        recipient = data.get("recipient")
        subject = data.get("subject")
        body = data.get("body")

        if not all([recipient, subject, body]):
            logger.error("Invalid message format: missing required fields")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        success = send_email(recipient, subject, body)
        if success:
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            # If email sending fails, reject the return self.order_repository.get_order_by_id(order_id)message and don't requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except json.JSONDecodeError:
        logger.error("Invalid JSON message received")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Unexpected error processing message: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consumer():
    """Start consuming messages from RabbitMQ"""
    while True:
        try:
            connection = setup_rabbit_connection()
            channel = connection.channel()

            # Declare queue with durability
            channel.queue_declare(queue="email_queue", durable=True)

            # Set up consumer
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue="email_queue", on_message_callback=process_email_request
            )

            logger.info("Email service started. Waiting for messages...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            logger.error("Lost connection to RabbitMQ. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            time.sleep(5)


if __name__ == "__main__":
    import threading

    # Start message consumer in a separate thread
    consumer_thread = threading.Thread(target=start_consumer)
    consumer_thread.daemon = True
    consumer_thread.start()

    # Start minimal Flask app for health checks
    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy", "service": "email-service"}, 200

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
