import logging
from uuid import uuid4
from typing import Dict, Optional, Callable, List
import websockets
import asyncio
from enum import Enum

from websockets.asyncio.client import ClientConnection
from pydantic import BaseModel

from resonitepy.client import to_class
from resonitepy.classes import ResoniteSession, ResoniteMessage, ResoniteHubUserStatus, ContactStatus, ResoniteContact
from resonitepy.endpoints import HUB_URL
from resonitepy import exceptions as resonite_exceptions
from resonitepy import signalr

class EventTarget(Enum):
    receiveStatusUpdate = ("ReceiveStatusUpdate", [ResoniteHubUserStatus])
    receiveSessionUpdate = ("ReceiveSessionUpdate", [ResoniteSession])
    messageSent = ("MessageSent", [ResoniteMessage])
    receivedMessage = ("ReceiveMessage", [ResoniteMessage])
    messagesRead = ("MessagesRead", [])
    remove_session = ("RemoveSession", [])
    contactAddedOrUpdated = ("ContactAddedOrUpdated", [ResoniteContact])

ACTIVATIONS = {
    EventTarget.receiveStatusUpdate:
        lambda hub: hub.invoke("RequestStatus", None, False),
}

class HubManager:

    def __init__(self, client_or_headers, cache: bool = True, cache_refresh_interval: float | None = 120):
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
        self._activated: set = set()
        self._cache_enabled = cache
        self._cache_refresh_interval = cache_refresh_interval
        self._contacts_cache: Optional[Dict[str, ResoniteContact]] = None
        self._refresh_task = None
        self._reader_task = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self):
        try:
            logging.info("Connecting to Resonite Hub...")
            self._websocket = await websockets.connect(
                HUB_URL,
                additional_headers=self.auth_headers,
            )

            # Send Handshake request
            await self._send_message(signalr.HandshakeRequest())
            # Wait for the server response
            try:
                first_frame = await asyncio.wait_for(self._websocket.recv(), timeout=5)
            except asyncio.TimeoutError as e:
                raise resonite_exceptions.ResoniteHubException("Handshake timed out") from e
            # Validate it
            leftover_messages = signalr.parse_handshake_response(first_frame)
            # Process any messages received at the same time
            for message in leftover_messages:
                await self._process_message(message)

            self._reader_task = asyncio.create_task(self._handle_messages())
            self._connected = True
            logging.info("Connected to Resonite Hub")

        except Exception as e:
            logging.error(f"Connection failed: {e!r}")
            await self.disconnect()
            raise

    async def disconnect(self):
        if self._websocket is None and not self._connected:
            return

        websocket, self._websocket = self._websocket, None

        self._connected = False
        self._activated.clear()
        if self._refresh_task is not None:
            self._refresh_task.cancel()
            self._refresh_task = None
        if self._reader_task is not None and self._reader_task is not asyncio.current_task():
            self._reader_task.cancel()
        self._reader_task = None

        if websocket is not None:
            await websocket.close()
        logging.info("Disconnected from Hub")

    def on(self, event_target: EventTarget, callback: Callable):
        self._handlers[event_target] = callback
        logging.debug(f"Registered handler for {event_target.value}")

    async def listen(self, *targets: EventTarget) -> None:
        wanted = targets or tuple(self._handlers)
        for target in wanted:
            activation = ACTIVATIONS.get(target)
            if activation is None or target in self._activated:
                continue
            await activation(self)
            self._activated.add(target)

    async def _handle_messages(self):
        try:
            async for frame in self._websocket:
                for message in signalr.split_messages(frame):
                    await self._process_message(message)
        except Exception as e:
            logging.error(f"Message handling error: {e!r}")
        finally:
            self._connected = False
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(
                        resonite_exceptions.ResoniteHubException("Hub connection closed")
                    )
            self._pending.clear()
            await self.disconnect()

    async def _process_message(self, message: signalr.HubMessage):
        match message:

            case signalr.Ping():
                logging.debug("Received ping")
                return

            case signalr.Invocation():
                target_name = message.target
                if target_name:
                    target = self._find_target(target_name)
                    if target is None:
                        logging.debug(f"No EventTarget mapped for hub event {target_name!r}")
                        return
                    wants_cache = (
                        self._cache_enabled
                        and target is EventTarget.contactAddedOrUpdated
                        and self._contacts_cache is not None
                    )
                    if target in self._handlers or wants_cache:
                        raw_args = message.arguments

                        _, arg_types = target.value
                        deserialized_args = self._deserialize_args(raw_args, arg_types or [])

                        if wants_cache and isinstance(deserialized_args[0], ResoniteContact):
                            self._contacts_cache[deserialized_args[0].id] = deserialized_args[0]

                        if target in self._handlers:
                            try:
                                handler = self._handlers[target]
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(deserialized_args)
                                else:
                                    handler(deserialized_args)
                            except Exception as e:
                                logging.error(f"Event handler error for {target}: {e!r}")

            case signalr.Completion():
                future = self._pending.get(message.invocationId)
                if future and not future.done():
                    if message.error:
                        future.set_exception(
                            resonite_exceptions.ResoniteHubException(message.error)
                        )
                    else:
                        future.set_result(message.result)
                return

            case signalr.Close():
                logging.error(f"Hub sent close: {message.error}")
                self._connected = False
                return
            case _:
                logging.warning(f"Unhandled hub message: {message!r}")

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
                    logging.warning(f"Failed to deserialize arg {i} to {arg_types[i]}: {e!r}")
                    deserialized.append(raw_arg)
            else:
                deserialized.append(raw_arg)

        return deserialized

    async def _send_message(self, message: BaseModel):
        await self._websocket.send(
            message.model_dump_json(exclude_none=True) + signalr.RECORD_SEPARATOR
        )

    async def send(self, target: str, *args):
        """ Invoke a hub function without waiting for a result (fire-and-forget).
        """
        if not self._connected:
            raise resonite_exceptions.ResoniteHubException("Hub is not connected")
        await self._send_message(signalr.Invocation(target=target, arguments=list(args)))

    async def invoke(self, target: str, *args, timeout: float = 5.0):
        """ Invoke a hub function and wait for its completion result.
        """
        if not self._connected:
            raise resonite_exceptions.ResoniteHubException("Hub is not connected")
        invocation_id = str(uuid4())
        future = asyncio.get_running_loop().create_future()
        self._pending[invocation_id] = future
        try:
            await self._send_message(
                signalr.Invocation(
                    target=target,
                    arguments=list(args),
                    invocationId=invocation_id
                )
            )
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            raise resonite_exceptions.ResoniteHubException(
                f"{target} invocation timed out after {timeout}s"
            )
        finally:
            self._pending.pop(invocation_id, None)  

    def _start_refresh_task(self):
        if self._cache_refresh_interval is None or self._refresh_task is not None:
            return
        self._refresh_task = asyncio.create_task(self._refresh_contacts_loop())

    async def _refresh_contacts_loop(self):
        while True:
            await asyncio.sleep(self._cache_refresh_interval)
            try:
                contacts = await self._fetch_contacts(timeout=5.0)
                self._contacts_cache = {contact.id: contact for contact in contacts}
            except Exception as e:
                logging.warning(f"Contact cache refresh failed: {e!r}")

    async def _fetch_contacts(self, timeout: float = 5.0) -> List[ResoniteContact]:
        """ Fetch contact list over the hub.
        """

        result = await self.invoke("InitializeStatus", timeout=timeout)
        raw_contacts = (result or {}).get("contacts")
        if raw_contacts is None:
            if self._client is None:
                raise resonite_exceptions.ResoniteHubException(
                    "InitializeStatus returned no contacts and no Client is "
                    "attached for the REST fallback"
                )
            logging.warning("InitializeStatus returned no contacts - falling back to REST")
            return await asyncio.to_thread(self._client.get_contacts, "rest")
        return [to_class(ResoniteContact, contact) for contact in raw_contacts]

    async def get_contacts(self, force: bool = False, timeout: float = 5.0) -> List[ResoniteContact]:
        """ Get contact list from cache.
        """
        if self._cache_enabled and not force and self._contacts_cache is not None:
            return list(self._contacts_cache.values())
        contacts = await self._fetch_contacts(timeout)
        if self._cache_enabled:
            self._contacts_cache = {contact.id: contact for contact in contacts}
            self._start_refresh_task()
        return contacts

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

        contacts = await asyncio.to_thread(self._client.get_contacts, "rest")
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