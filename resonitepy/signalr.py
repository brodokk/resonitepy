import logging
from typing import Annotated, Any, Literal
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from resonitepy import exceptions as resonite_exceptions

RECORD_SEPARATOR = "\x1e"

class HandshakeRequest(BaseModel):
    protocol: Literal["json"] = "json"
    version: Literal[1] = 1

class HandshakeResponse(BaseModel):
    error: str | None = None

class Invocation(BaseModel):
    type: Literal[1] = 1
    target: str
    arguments: list = []
    invocationId: str | None = None

class Completion(BaseModel):
    type: Literal[3] = 3
    invocationId: str
    result: Any = None
    error: str | None = None

class Ping(BaseModel):
    type: Literal[6] = 6

class Close(BaseModel):
    type: Literal[7] = 7
    error: str | None = None
    allowReconnect: bool = False


HubMessage = Annotated[
    Invocation
    | Completion
    | Ping
    | Close,
    Field(discriminator="type")
]
_HUB_MESSAGE_ADAPTER = TypeAdapter(HubMessage)

def split_messages(ws_frame: str) -> list[HubMessage]:
    messages = []
    parts = ws_frame.split(RECORD_SEPARATOR)
    for part in parts:
        if part.strip():
            try:
                data = _HUB_MESSAGE_ADAPTER.validate_json(part)
                messages.append(data)
            except ValidationError:
                logging.warning(f"Non-JSON message: {part!r}")
    return messages

def parse_handshake_response(ws_frame: str) -> list[HubMessage]:
    messages = [p for p in ws_frame.split(RECORD_SEPARATOR) if p.strip()]
    if not messages:
        raise resonite_exceptions.ResoniteHubException(f"No handshake received: {ws_frame!r}")
    try:
        handshake_response = HandshakeResponse.model_validate_json(messages[0])
    except ValidationError as e:
        raise resonite_exceptions.ResoniteHubException(f"Invalid handshake failed: {messages[0]!r}") from e
    if handshake_response.error is not None:
        raise resonite_exceptions.ResoniteHubException(f"Hub did not accept the handshake: {handshake_response.error}")
    return split_messages(RECORD_SEPARATOR.join(messages[1:]))
    