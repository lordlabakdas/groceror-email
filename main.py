import logging
import threading

import uvicorn

import config
from api import app
from consumer import start as start_consumer
from mailer import Mailer

logging.basicConfig(level=logging.INFO)


def main() -> None:
    mailer = Mailer()
    t = threading.Thread(target=start_consumer, args=(mailer,), daemon=True)
    t.start()
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT, log_level="info")


if __name__ == "__main__":
    main()
