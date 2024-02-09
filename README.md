# resonitepy

Unofficial Resonite API python library.

Based on a work by [neosvrpy](https://github.com/brodokk/neosvrpy).

The code is still in WIP mode, see the files `resonitepy/classes.py` and
`resonitepy/client.py` for how to use them. The SignalR protocol is yet
to be fully implemented.

## Usage

Quick exemple of to use it

```
from resonitepy.client import Client
from resonitepy.classes import LoginDetails, LoginDetailsAuth

client = Client()

client.login(
    LoginDetails(
        username="YOURUSERNAME",
        authentication=LoginDetailsAuth(password="YOURPASSWORD"),
    )
)


friends = client.getContacts()
for friend in friends:
    print(friend.contactUsername)
```
