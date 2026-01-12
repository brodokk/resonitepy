"""
Tool to quickly test if the endpoints input and output are still matching with the code.

For not this script have just in mind to detect if some class have field that are missing or of invalid type.

Usage:
    OWNERID=<Resonite U- user id> PASSWORD=<your password> python test.py

TODO:
    - Add support for field in model but not send anymore, and raise an error too

"""

import os

os.environ['DEBUG'] = 'true'

from resonitepy.classes import ResoniteDirectory, ResoniteLink, ResoniteMessage, ResoniteMessageContentText
from resonitepy.client import Client
from resonitepy.exceptions import ResoniteException, ResoniteAPIException, InvalidToken
from resonitepy import classes

client = Client()

import tomllib

with open("testconf.toml", mode="rb") as fp:
    config = tomllib.load(fp)

client.login(
    classes.LoginDetails(
        ownerId=config.get('owner_id'),
        authentication=classes.LoginDetailsAuth(password=config.get('password')),
    )
)

user = client.getUserData()
user_groups = client.getMemberships()
badges = client.badges()
sessions = client.getSessions()
session = client.getSession(sessions[0].sessionId)
contacts = client.getContacts()
inventory = client.getInventory()
# for record in inventory:
#     # TODO: test about ResoniteObject
#     if isinstance(record, ResoniteDirectory):
#         client.getDirectory(record)
#     if isinstance(record, ResoniteLink):
#         try:
#             client.resolveLink(record)
#         except ResoniteAPIException as e:
#             if '404' in str(e):
#                 print("Folder either delete or made non public. Impossible to know for sure.")
#             else:
#                 print(record)
#                 raise e
#         except InvalidToken as e:
#             print("Supposed denied permission on an existing public folder. Impossible to know for sure.")
#         except ResoniteException as e:
#             if "Not supported scheme 'https' for link type" in str(e):
#                 print("https scheme for ResoniteLink is not supported for now.")
#             else:
#                 print(record)
#                 raise e
legacy_messages = client.getMessageLegacy()
owner_path_user = client.getOwnerPath(client.userId)
owner_path_group = client.getOwnerPath(user_groups[0].id)
group = client.getGroup(user_groups[0].id)
group_members = client.getGroupMembers(user_groups[0].id)
group_member = client.getGroupMember(user_groups[0].id, group_members[0].id)
cloud_vars = client.listCloudVar(client.userId)

# TODO: Find something a bit more public (as visible and editable for everyone)
cloud_var_def = client.getCloudVarDefs(client.userId, 'U-brodokk.avatar.config.snoot')
cloud_var = client.getCloudVar(client.userId, 'U-brodokk.avatar.config.snoot')
client.setCloudVar(client.userId, 'U-brodokk.avatar.config.snoot', 'true')
client.setCloudVar(client.userId, 'U-brodokk.avatar.config.snoot', 'false')
cloud_var = client.getCloudVar(client.userId, 'U-brodokk.avatar.config.snoot')

search_result = client.searchUser('brodokk')
user = client.getUser(contacts[0].id)
user = client.getUserByName(contacts[0].contactUsername)

platform = client.platform()
