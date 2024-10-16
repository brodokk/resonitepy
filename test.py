"""
Tool to quickly test if the endpoints input and output are still matching with the code.

For not this script have just in mind to detect if some class have field that are missing or of invalid type.

Usage:
    OWNERID=<Resonite U- user id> PASSWORD=<your password> python test.py

TODO:
    - Add support for field in model but not send anymore, and raise an error too

"""

import os

from resonitepy.classes import ResoniteDirectory, ResoniteLink, ResoniteMessage, ResoniteMessageContentText
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
user_groups = client.getMemberships()
sessions = client.getSessions()
session = client.getSession(sessions[0].sessionId)
contacts = client.getContacts()
inventory = client.getInventory()
tested_directory = False
tested_link = False
for record in inventory:
    # TODO: test about ResoniteObject
    if not tested_directory and isinstance(record, ResoniteDirectory):
        directory = client.getDirectory(record)
        tested_directory = True
    # TODO: Can't test, brodokk doesn't have this kind of record in his inventory
    if not tested_link and isinstance(record, ResoniteLink) and record.assetUri.path.startswith('U-'):
        link = client.resolveLink(record)
        tested_link = True
    if tested_directory and tested_link:
        break
legacy_messages = client.getMessageLegacy()
owner_path_user = client.getOwnerPath(client.userId)
owner_path_group = client.getOwnerPath(user_groups[0].id)
group = client.getGroup(user_groups[0].id)
group_members = client.getGroupMembers(user_groups[0].id)
group_member = client.getGroupMember(user_groups[0].id, group_members[0].id)

# TODO: VERY IMPORTANT I NEED TO CONTINUE THIS AND PATCH MORE STUFF IF NEEDED BEFORE DOING A RELEASE!
platform = client.platform()
