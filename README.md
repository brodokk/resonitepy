# neos.py

Unofficial NeosVR API python library.

Based on a work by [mralext20](https://github.com/mralext20/neos.py). The main
difference with his library is the simplification of the HTTP call by make them
sync instead of async but is more up to date.

The code is still in WIP mode, see the files `neos/classes.py` and
`neos/client.py` for how to use them.

## Usage

Quick exemple of to use it

```
from neos.client import Client
from neos.classes import LoginDetails

client = Client()

client.login(
    LoginDetails(username="YOURUSERNAME", password="YOURPASSWORD")
)

friends = client.getFriends()
for friend in friends:
    print(friend.friendUsername
```
