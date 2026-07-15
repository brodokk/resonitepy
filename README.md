# resonitepy

Unofficial Resonite API python library (HTTP + SignalR hub). Sync and async.

Based on a work by [neosvrpy](https://github.com/brodokk/neosvrpy).

The code is still in WIP mode, see the files `resonitepy/classes.py` and
`resonitepy/client.py` for how to use them. The SignalR protocol is yet
to be fully implemented.

## Install

`poetry install`

## Basuc Usage (sync)

```python
from resonitepy.client import Client
from resonitepy.classes import LoginDetails, LoginDetailsAuth

client = Client()
client.login(LoginDetails(
    ownerId="U-yourUserId",
    authentication=LoginDetailsAuth(password="your password"),
))

for contact in client.getContacts():
    print(contact.contactUsername, contact.contactStatus)
```

## Async with live events (via SignalR hub)

```python
import asyncio
from resonitepy.client import Client
from resonitepy.classes import LoginDetails, LoginDetailsAuth
from resonitepy.hub_manager import HubManager, EventTarget

async def main():
    client = Client()
    client.login(LoginDetails(
        ownerId="U-yourUserId",
        authentication=LoginDetailsAuth(password="your password"),
    ))
    hub = HubManager(client)
    await hub.connect()

    def on_message(args):
        print(args[0])

    hub.on(EventTarget.receivedMessage, on_message)
    await asyncio.sleep(3600)
    await hub.disconnect()

asyncio.run(main())
```