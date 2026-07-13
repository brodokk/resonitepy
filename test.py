"""
Tool to quickly test if the endpoints input and output are still matching with the code.

For not this script have just in mind to detect if some class have field that are missing or of invalid type.

Usage:
    OWNERID=<Resonite U- user id> PASSWORD=<your password> python test.py

TODO:
    - Add support for field in model but not send anymore, and raise an error too

"""

import os
import sys
from datetime import datetime

os.environ['DEBUG'] = 'true'

from resonitepy.classes import ResoniteDirectory, ResoniteLink, ResoniteObject, ResoniteWorld, ResoniteTexture, ResoniteAudio, ResoniteMessage, ResoniteMessageContentText
from resonitepy.client import Client
from resonitepy.exceptions import ResoniteException, ResoniteAPIException, InvalidToken
from resonitepy import classes

LOG_PATH = f"test_logs/test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


class MultiWriter:

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)

    def flush(self):
        for stream in self.streams:
            stream.flush()


log_file = open(LOG_PATH, "w")
sys.stdout = MultiWriter(sys.stdout, log_file)
sys.stderr = MultiWriter(sys.stderr, log_file)

client = Client()

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # Python 3.10 fallback

with open("testconf.toml", mode="rb") as fp:
    config = tomllib.load(fp)

client.login(
    classes.LoginDetails(
        ownerId=config.get('owner_id'),
        authentication=classes.LoginDetailsAuth(password=config.get('password')),
    )
)

user = client.getUserData()
print(f"getUserData response: {user}")
for entitlement in (user.entitlements or []):
    print(f"entitlement ({type(entitlement).__name__}): {entitlement}")
for supporter_metadata in (user.supporterMetadata or []):
    print(f"supporterMetadata ({type(supporter_metadata).__name__}): {supporter_metadata}")

user_groups = client.getMemberships()
print(f"getMemberships response: {user_groups}")

badges = client.badges()
print(f"badges response: {badges}")

sessions = client.getSessions()
print(f"getSessions response: {sessions}")

if sessions:
    session = client.getSession(sessions[0].sessionId)
    print(f"getSession response: {session}")
else:
    print("No sessions to call getSession on, skipping.")

contacts = client.getContacts()
print(f"Got {len(contacts)} contacts")
for contact in contacts:
    print(
        f"- {contact.contactUsername} ({contact.id}): "
        f"status={contact.contactStatus}, accepted={contact.isAccepted}, "
        f"pronouns={contact.profile.pronouns if contact.profile else None}, "
        f"tagline={contact.profile.tagline if contact.profile else None}, "
        f"latestMessageTime={contact.latestMessageTime}"
    )

icon_url = next((c.profile.iconUrl for c in contacts if c.profile and c.profile.iconUrl), None)
if icon_url:
    signature = client.res_db_signature(icon_url)
    print(f"res_db_signature({icon_url}) response: {signature}")
    http_url = client.res_db_to_http(icon_url)
    print(f"res_db_to_http({icon_url}) response: {http_url}")
else:
    print("No contact profile iconUrl available, skipping res_db_signature/res_db_to_http.")

inventory = client.getInventory()
print(f"getInventory response: {inventory}")
for record in inventory:
    if isinstance(record, ResoniteDirectory):
        client.getDirectory(record)
    if isinstance(record, ResoniteObject):
        print(f"ResoniteObject: {record.name} ({record.id}) -> {record.assetUri}")
    if isinstance(record, ResoniteWorld):
        print(f"ResoniteWorld: {record.name} ({record.id}) -> {record.assetUri}")
    if isinstance(record, ResoniteTexture):
        print(f"ResoniteTexture: {record.name} ({record.id}) -> {record.assetUri}")
    if isinstance(record, ResoniteAudio):
        print(f"ResoniteAudio: {record.name} ({record.id}) -> {record.assetUri}")
    if isinstance(record, ResoniteLink):
        try:
            client.resolveLink(record)
        except ResoniteAPIException as e:
            if '404' in str(e):
                print("Folder either delete or made non public. Impossible to know for sure.")
            else:
                print(record)
                raise e
        except InvalidToken as e:
            print("Supposed denied permission on an existing public folder. Impossible to know for sure.")
        except ResoniteException as e:
            if "Not supported scheme 'https' for link type" in str(e):
                print("https scheme for ResoniteLink is not supported for now.")
            else:
                print(record)
                raise e

legacy_messages = client.getMessageLegacy()
print(f"getMessageLegacy response: {legacy_messages}")
for message in legacy_messages:
    print(f"message type={message.messageType}, content ({type(message.content).__name__}): {message.content}")

owner_path_user = client.getOwnerPath(client.userId)
print(f"getOwnerPath response: {owner_path_user}")

search_result = client.searchUser(config.get('search_query'))
print(f"searchUser response: {search_result}")

user = client.getUser(contacts[0].id)
print(f"getUser response: {user}")

user = client.getUserByName(contacts[0].contactUsername)
print(f"getUserByName response: {user}")

platform = client.platform()
print(f"platform response: {platform}")

if config.get('group_id'):
    owner_path_group = client.getOwnerPath(config.get('group_id'))
    print(f"getOwnerPath response: {owner_path_group}")
    group = client.getGroup(config.get('group_id'))
    print(f"getGroup response: {group}")
    group_members = client.getGroupMembers(config.get('group_id'))
    print(f"getGroupMembers response: {group_members}")
    if group_members:
        group_member = client.getGroupMember(config.get('group_id'), group_members[0].id)
        print(f"getGroupMember response: {group_member}")
    else:
        print("No group members to call getGroupMember on, skipping.")
else:
    print("No group_id in testconf.toml, skipping group tests.")

# Cloud var used for testing need to be created on a account used for running tests
# To be set via messages to the Resonite Bot (see https://wiki.resonite.com/Cloud_Variables)
# Harcoded path to ne clearly namespaced on the account they're run against
# Commands to run:
#   /createUserVar resonitepy_test
#   /setUserVarType resonitepy_test bool
#   /setUserVarDefaultValue resonitepy_test false
#   /setUserVarPerms resonitepy_test read,write variable_owner_unsafe
cloud_vars = client.listCloudVar(client.userId)
print(f"listCloudVar response: {cloud_vars}")
cloud_var_def = client.getCloudVarDefs(client.userId, f"{client.userId}.resonitepy_test")
print(f"getCloudVarDefs response: {cloud_var_def}")
cloud_var = client.getCloudVar(client.userId, f"{client.userId}.resonitepy_test")
print(f"getCloudVar response: {cloud_var}")
client.setCloudVar(client.userId, f"{client.userId}.resonitepy_test", 'true')
cloud_var = client.getCloudVar(client.userId, f"{client.userId}.resonitepy_test")
print(f"getCloudVar response after setting true: {cloud_var}")
client.setCloudVar(client.userId, f"{client.userId}.resonitepy_test", 'false')
cloud_var = client.getCloudVar(client.userId, f"{client.userId}.resonitepy_test")
print(f"getCloudVar response after setting false: {cloud_var}")
