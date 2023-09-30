# resonitepy

Unofficial Resonite API python library.

Based on a work by [neosvrpy](https://github.com/brodokk/neosvrpy).

The code is still in WIP mode, see the files `resonitepy/classes.py` and
`resonitepy/client.py` for how to use them.

## Usage

Quick exemple of to use it

```
from resonitepy.client import Client
from resonitepy.classes import LoginDetails

client = Client()

client.login(
    LoginDetails(username="YOURUSERNAME", password="YOURPASSWORD")
)

friends = client.getFriends()
for friend in friends:
    print(friend.friendUsername)
```
