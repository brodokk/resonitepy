import logging
from uuid import uuid4
from typing import Dict, Optional, Callable, List
import websockets
import json
import asyncio
from enum import Enum

from websockets.asyncio.client import ClientConnection

from resonitepy.client import to_class
from resonitepy.classes import ResoniteSession, ResoniteMessage, ResoniteHubUserStatus, ContactStatus, ResoniteContact
from resonitepy.endpoints import HUB_URL
from resonitepy import exceptions as resonite_exceptions

class EventType(Enum):
    undefined = 0
    invocation = 1
    streamItem = 2
    completion = 3
    streamInvocation = 4
    cancelInvocation = 5
    ping = 6
    close = 7

class EventTarget(Enum):
    receiveStatusUpdate = ("ReceiveStatusUpdate", [ResoniteHubUserStatus])
    receiveSessionUpdate = ("ReceiveSessionUpdate", [ResoniteSession])
    messageSent = ("MessageSent", [ResoniteMessage])
    receivedMessage = ("ReceiveMessage", [ResoniteMessage])
    messagesRead = ("MessagesRead", [])
    remove_session = ("RemoveSession", [])
    contactAddedOrUpdated = ("ContactAddedOrUpdated", [ResoniteContact])

class HubManager:

    def __init__(self, client_or_headers):
        if isinstance(client_or_headers, dict):
            self._client = None
            self.auth_headers = client_or_headers
        else:
            self._client = client_or_headers
            self.auth_headers = client_or_headers.headers
        self._handlers: Dict[EventTarget, Callable] = {}
        self._pending: Dict[str, asyncio.Future] = {}
        self._websocket: Optional[ClientConnection] = None
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
            logging.info("Connected to Resonite Hub")

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
        logging.debug(f"Registered handler for {event_target.value}")

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
        finally:
            self._connected = False
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(
                        resonite_exceptions.ResoniteHubException("Hub connection closed")
                    )
            self._pending.clear()

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

        if msg_type == EventType.completion.value:
            future = self._pending.get(data.get("invocationId"))
            if future and not future.done():
                if data.get("error"):
                    future.set_exception(
                        resonite_exceptions.ResoniteHubException(data["error"])
                    )
                else:
                    future.set_result(data.get("result"))
            return

        if msg_type == EventType.close.value:
            logging.error(f"Hub sent close: {data.get('error')}")
            return

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
                    deserialized_obj = to_class(arg_types[i], raw_arg)
                    deserialized.append(deserialized_obj)
                except Exception as e:
                    logging.warning(f"Failed to deserialize arg {i} to {arg_types[i]}: {e}")
                    deserialized.append(raw_arg)
            else:
                deserialized.append(raw_arg)

        return deserialized

    async def send(self, target: str, *args):
        """ Invoke a hub function without waiting for a result (fire-and-forget).
        """
        if not self._connected:
            raise resonite_exceptions.ResoniteHubException("Hub is not connected")
        frame = {"type": EventType.invocation.value, "target": target, "arguments": list(args)}
        await self._websocket.send(json.dumps(frame) + self._eof)

    async def invoke(self, target: str, *args, timeout: float = 5.0):
        """ Invoke a hub function and wait for its completion result.
        """
        if not self._connected:
            raise resonite_exceptions.ResoniteHubException("Hub is not connected")
        invocation_id = str(uuid4())
        future = asyncio.get_running_loop().create_future()
        self._pending[invocation_id] = future
        frame = {
            "type": EventType.invocation.value,
            "invocationId": invocation_id,
            "target": target,
            "arguments": list(args),
        }
        try:
            await self._websocket.send(json.dumps(frame) + self._eof)
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            raise resonite_exceptions.ResoniteHubException(
                f"{target} invocation timed out after {timeout}s"
            )
        finally:
            self._pending.pop(invocation_id, None)

    async def add_contact(self, user_id: str, timeout: float = 5.0):
        """ Send a contact request to a user, or accept a pending one.
        """
        await self.set_contact_status(user_id, ContactStatus.ACCEPTED, timeout)

    async def accept_contact_request(self, user_id: str, timeout: float = 5.0):
        """ Accept a pending contact request.
        """
        await self.set_contact_status(user_id, ContactStatus.ACCEPTED, timeout)
    
    async def decline_contact_request(self, user_id: str, timeout: float = 5.0):
        """ Decline a pending contact request.
        """
        await self.set_contact_status(user_id, ContactStatus.IGNORED, timeout)

    async def remove_contact(self, user_id: str, timeout: float = 5.0):
        """ Remove a contact.

        Using `Ignored` to match the official Resonite client behavior
        (anti-abuse, see https://github.com/Yellow-Dog-Man/Resonite-Issues/issues/4035#issuecomment-2770449855)
        There will be no notification of any new pending request to accept for this user.

        To enable the ability to receive a notification for any new pending request for this
        user in the future use the function use set_contact_status(user_id,
        ContactStatus.NONE).
        """
        await self.set_contact_status(user_id, ContactStatus.IGNORED, timeout)

    async def set_contact_status(self, user_id: str, status: ContactStatus, timeout: float):
        """ Set current user side of the contact relationship to an explicit status.

        Prefer the intented methods (add_contact, accept_contact_request, decline_contact_request,
        remove_contact) as they follow the official Resonite client behavior. Statues:

        - ACCEPTED: send a contact request or accept a pending one.
        - IGNORED: decline or remove a contact, future requests are silently muted.
        - NONE: full reset, the user can send a new request again later.
        - BLOCKED: no behavior known so far, worked as IGNORED.
        - REQUESTED: set by the server on the receiving side, can be set manually turning the
        relationship into a pending request on receiving side, no change on sending side.
        """

        if self._client is None:
            raise resonite_exceptions.ResoniteHubException(
                "Contact operations need HubManager(client) with a logged-in Client"
            )

        contacts = await asyncio.to_thread(self._client.getContacts)
        existing = next((c for c in contacts if c.id == user_id), None)
        if existing is not None:
            username = existing.contactUsername
            is_accepted = existing.isAccepted
            latest_message_time = existing.latestMessageTime.isoformat()
        else:
            user = await asyncio.to_thread(self._client.getUser, user_id)
            username = user.username
            is_accepted = False
            latest_message_time = "1970-01-01T00:00:00Z"

        payload = {
            "id": user_id,
            "contactUsername": username,
            "ownerId": self._client.userId,
            "contactStatus": status.value,
            "isAccepted": is_accepted,
            "userStatus": {},
            "profile": {},
            "latestMessageTime": latest_message_time,
        }
        result = await self.invoke("UpdateContact", payload, timeout=timeout)
        if result is not True:
            raise resonite_exceptions.ResoniteHubException(
                f"UpdateContact reject for {user_id}: {result}" 
            )