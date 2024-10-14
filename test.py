"""
Tool to quickly test if the endpoints input and output are still matching with the code.

For not this script have just in mind to detect if some class have field that are missing or of invalid type.

Usage:
    OWNERID=<Resonite U- user id> PASSWORD=<your password> python test.py

"""

import os

from resonitepy.client import Client
from resonitepy import classes

client = Client()

os.environ['DEBUG'] = 'true'

client.login(
    classes.LoginDetails(
        ownerId=os.environ.get('OWNERID'),
        authentication=classes.LoginDetailsAuth(password=os.environ.get('PASSWORD')),
    )
)

user = client.getUserData()
sessions = client.getSessions()
session = client.getSession(sessions[0].sessionId)
contacts = client.getContacts()
inventory = client.getInventory()
platform = client.platform()