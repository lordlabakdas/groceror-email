from typing import Literal

from pydantic import BaseModel

SUPPORTED_SCHEMA_VERSIONS = {"1.0"}


class EmailMessage(BaseModel):
    schema_version: str = "1.0"
    event: Literal["send_email"]
    recipient: str
    subject: str
    body: str


def parse_message(data: dict) -> EmailMessage:
    version = data.get("schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(f"Unsupported schema_version: {version!r}")

    if data.get("event") != "send_email":
        raise ValueError(f"Unknown event type: {data.get('event')!r}")

    return EmailMessage(**data)
