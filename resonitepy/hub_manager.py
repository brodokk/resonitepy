import logging
from typing import Dict, Optional, Callable, List
import websockets
import json
import asyncio
from enum import Enum

from resonitepy.client import DACITE_CONFIG, to_class
from resonitepy.classes import ResoniteSession, ResoniteSession, ResoniteMessage
from resonitepy.endpoints import HUB_URL


class EventType(Enum):
    invocation = 1
    streamItem = 2
    completion = 3
    streamInvocation = 4
    cancelInvocation = 5
    ping = 6
    close = 7
    undefined = 1

class EventTarget(Enum):
    receiveStatusUpdate = ("ReceiveStatusUpdate", [ResoniteSession])
    receiveSessionUpdate = ("ReceiveSessionUpdate", [ResoniteSession])
    messageSent = ("MessageSent", [ResoniteMessage])
    receivedMessage = ("ReceiveMessage", [ResoniteMessage])
    messageRead = ("MessageRead", [])
    remove_session = ("RemoveSession", [])

class HubManager:

    def __init__(self, auth_headers: Dict[str, str]):
        self.auth_headers = auth_headers
        self._handlers: Dict[EventTarget, Callable] = {}
        self._websocket: Optional[websockets.WebSocketServerProtocol] = None
        self._connected = False
        self._eof = "\x1e"

    async def connect(self):
        try:
            logging.info("Connecting to Resonite Hub...")
            self._websocket = await websockets.connect(
                HUB_URL,
                additional_headers=self.auth_headers,
            )

            # Send negotiation
            negotiation = json.dumps({"protocol": "json", "version": 1}) + self._eof
            await self._websocket.send(negotiation)

            # Start message handling
            asyncio.create_task(self._handle_messages())
            self._connected = True
            logging.info("COnnected to Resonite Hub")

        except Exception as e:
            logging.error(f"Connection failed: {e}")
            raise
    async def disconnect(self):
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
        self._connected = False
        logging.info("Disconnected from Hub")

    def on(self, event_target: EventTarget, callback: Callable):
        self._handlers[event_target] = callback
        logging.debug(f"Registred handler for {event_target.value}")

    async def _handle_messages(self):
        try:
            async for message in self._websocket:
                logging.info(f"Received: {repr(message)}")

                # Parse multiple messages
                parts = message.split(self._eof)
                for part in parts:
                    if part.strip():
                        try:
                            data = json.loads(part)
                            logging.info(f"Parsed: {json.dumps(data, indent=2)}")
                            await self._process_message(data)
                        except json.JSONDecodeError:
                            logging.warning(f"Non-JSON message: {part}")
        except Exception as e:
            logging.error(f"Message handling error: {e}")

    async def _process_message(self, data: Dict):
        msg_type = data.get("type", -1)

        if msg_type == EventType.ping.value:
            logging.debug("Received ping")
            return

        if msg_type == EventType.invocation.value:
            target_name = data.get("target")
            if target_name:
                target = self._find_target(target_name)
                if target and target in self._handlers:
                    raw_args = data.get("arguments", [])

                    _, arg_types = target.value
                    deserialized_args = self._deserialize_args(raw_args, arg_types or [])

                    try:
                        handler = self._handlers[target]
                        if asyncio.iscoroutinefunction(handler):
                            await handler(deserialized_args)
                        else:
                            handler(deserialized_args)
                    except Exception as e:
                        logging.error(f"Event handler error for {target}: {e}")

    def _find_target(self, target_name: str) -> Optional[EventTarget]:
        """Find EventTarget enum by target name"""
        for target in EventTarget:
            target_str, _ = target.value
            if target_str == target_name:
                return target
        return None

    def _deserialize_args(self, raw_args: List, arg_types: List):
        deserialized = []

        for i, raw_arg in enumerate(raw_args):
            if i < len(arg_types) and arg_types[i] is not None:
                try:
                    deserialized_obj = to_class(arg_types[i], raw_arg, DACITE_CONFIG)
                    deserialized.append(deserialized_obj)
                except Exception as e:
                    logging.warning(f"Failed to deserialize arg {i} to {arg_types[i]}: {e}")
                    deserialized.append(raw_arg)
            else:
                deserialized.append(raw_arg)

        return deserialized