import asyncio
import websockets
import json
import logging

import tomllib

from resonitepy.hub_manager import EventTarget

EOF = "\x1e"  # SignalR EOF character

from resonitepy.client import Client
from resonitepy import classes
from resonitepy.hub_manager import HubManager

with open("testconf.toml", mode="rb") as fp:
    config = tomllib.load(fp)

async def debug_con_with_hub():
    client = Client()
    client.login(
        classes.LoginDetails(
            ownerId=config.get('owner_id'),
            authentication=classes.LoginDetailsAuth(password=config.get('password')),
        )
    )

    headers = client.headers
    hub = HubManager(client.headers)

    await hub.connect()

    def handle_receive_message(args):
        print(f"Message received: {args}")
    hub.on(EventTarget.receivedMessage, handle_receive_message)

    def handle_message_sent(args):
        print(f"Message received: {args}")
    hub.on(EventTarget.messageSent, handle_message_sent)

    def handle_status_update(args):
        print(f"Status Update received: {args}")
    hub.on(EventTarget.receiveSessionUpdate, handle_status_update)

    def handle_sessions_update(args):
        print(f"Sessions Update received: {args}")
    hub.on(EventTarget.receiveSessionUpdate, handle_sessions_update)

    print("Connected! Waiting for messages...")
    await asyncio.sleep(60)

    await hub.disconnect()

if __name__ == "__main__":
    asyncio.run(debug_con_with_hub())