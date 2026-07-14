"""
Tool to quickly test if the endpoints input and output are still matching with the code.

For not this script have just in mind to detect if some class have field that are missing or of invalid type.

Usage:
    OWNERID=<Resonite U- user id> PASSWORD=<your password> python test.py

TODO:
    - Add support for field in model but not send anymore, and raise an error too

"""

import dataclasses
import os
import sys
from datetime import datetime
from enum import Enum

os.environ["RESONITEPY_DRIFT"] = "1"

from resonitepy.classes import ResoniteDirectory, ResoniteLink, ResoniteObject, ResoniteWorld, ResoniteTexture, ResoniteAudio, ResoniteMessage, ResoniteMessageContentText
from resonitepy.client import Client, to_class
from resonitepy.exceptions import ResoniteException, ResoniteAPIException, InvalidToken
from resonitepy import classes

LOG_PATH = f"test_logs/test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

DRIFT = []
DRIFT_OPTIONAL = []
CLASS_SENT = {}


def collect_drift(obj, path=""):
    """ Returns every place where obj holds API data this module doesn't know about.
    """
    found = []
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        cls = type(obj)
        if cls.__name__.endswith("Unknown"):
            found.append(f"{path or '<root>'}: API sent an unknown type, parsed as {cls.__name__}: {vars(obj)}")
        sent = getattr(obj, "__api_fields__", None)
        if sent is not None:
            CLASS_SENT.setdefault(cls, set()).update(sent)
        declared = {f.name for f in dataclasses.fields(obj)}
        for key, value in vars(obj).items():
            if key not in declared and not key.startswith("_"):
                found.append(f"{path}.{key}: API sends this field but {cls.__name__} doesn't declare it (value: {value!r})")
        for f in dataclasses.fields(obj):
            found.extend(collect_drift(getattr(obj, f.name), f"{path}.{f.name}"))
    elif isinstance(obj, Enum):
        if obj.name == "UNKNOWN":
            found.append(f"{path}: API sent an unknown value, parsed as {type(obj).__name__}.UNKNOWN")
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            found.extend(collect_drift(item, f"{path}[{i}]"))
    elif isinstance(obj, dict):
        for key, value in obj.items():
            found.extend(collect_drift(value, f"{path}[{key!r}]"))
    return found


def check(result, label):
    findings = collect_drift(result, label)
    for finding in findings:
        print(f"[DRIFT] {finding}")
    DRIFT.extend(findings)
    return result

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

user = check(client.getUserData(), "getUserData")
print(f"getUserData response: {user}")
for entitlement in (user.entitlements or []):
    print(f"entitlement ({type(entitlement).__name__}): {entitlement}")
for supporter_metadata in (user.supporterMetadata or []):
    print(f"supporterMetadata ({type(supporter_metadata).__name__}): {supporter_metadata}")

user_groups = check(client.getMemberships(), "getMemberships")
print(f"getMemberships response: {user_groups}")

badges = check(client.badges(), "badges")
print(f"badges response: {badges}")

sessions = check(client.getSessions(), "getSessions")
print(f"getSessions response: {sessions}")

if sessions:
    session = check(client.getSession(sessions[0].sessionId), "getSession")
    print(f"getSession response: {session}")
else:
    print("No sessions to call getSession on, skipping.")

contacts = check(client.getContacts(), "getContacts")
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

inventory = check(client.getInventory(), "getInventory")
print(f"getInventory response: {inventory}")
for record in inventory:
    if isinstance(record, ResoniteDirectory):
        check(client.getDirectory(record), "getDirectory")
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
            check(client.resolveLink(record), "resolveLink")
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

legacy_messages = check(client.getMessageLegacy(), "getMessageLegacy")
print(f"getMessageLegacy response: {legacy_messages}")
for message in legacy_messages:
    print(f"message type={message.messageType}, content ({type(message.content).__name__}): {message.content}")

owner_path_user = check(client.getOwnerPath(client.userId), "getOwnerPath")
print(f"getOwnerPath response: {owner_path_user}")

search_result = check(client.searchUser(config.get('search_query')), "searchUser")
print(f"searchUser response: {search_result}")

user = check(client.getUser(contacts[0].id), "getUser")
print(f"getUser response: {user}")

user = check(client.getUserByName(contacts[0].contactUsername), "getUserByName")
print(f"getUserByName response: {user}")

platform = check(client.platform(), "platform")
print(f"platform response: {platform}")

if config.get('group_id'):
    owner_path_group = check(client.getOwnerPath(config.get('group_id')), "getOwnerPath(group)")
    print(f"getOwnerPath response: {owner_path_group}")
    group = check(client.getGroup(config.get('group_id')), "getGroup")
    print(f"getGroup response: {group}")
    group_members = check(client.getGroupMembers(config.get('group_id')), "getGroupMembers")
    print(f"getGroupMembers response: {group_members}")
    if group_members:
        group_member = check(client.getGroupMember(config.get('group_id'), group_members[0].id), "getGroupMember")
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
cloud_vars = check(client.listCloudVar(client.userId), "listCloudVar")
print(f"listCloudVar response: {cloud_vars}")
cloud_var_def = check(client.getCloudVarDefs(client.userId, f"{client.userId}.resonitepy_test"), "getCloudVarDefs")
print(f"getCloudVarDefs response: {cloud_var_def}")
cloud_var = check(client.getCloudVar(client.userId, f"{client.userId}.resonitepy_test"), "getCloudVar")
print(f"getCloudVar response: {cloud_var}")
client.setCloudVar(client.userId, f"{client.userId}.resonitepy_test", 'true')
cloud_var = check(client.getCloudVar(client.userId, f"{client.userId}.resonitepy_test"), "getCloudVar")
print(f"getCloudVar response after setting true: {cloud_var}")
client.setCloudVar(client.userId, f"{client.userId}.resonitepy_test", 'false')
cloud_var = check(client.getCloudVar(client.userId, f"{client.userId}.resonitepy_test"), "getCloudVar")
print(f"getCloudVar response after setting false: {cloud_var}")

for cls, sent in CLASS_SENT.items():
    for field_name, info in cls.__pydantic_fields__.items():
        api_name = info.alias or field_name
        if api_name not in sent:
            DRIFT_OPTIONAL.append(f"{cls.__name__}.{field_name}: declared in model but the API never sent it")

print()
if DRIFT_OPTIONAL:
    print(f"=== {len(DRIFT_OPTIONAL)} optional drift finding(s) ===")
    for finding in DRIFT_OPTIONAL:
        print(f"  {finding}")
if DRIFT:
    print(f"=== {len(DRIFT)} drift finding(s) ===")
    for finding in DRIFT:
        print(f"  {finding}")
if not DRIFT and not DRIFT_OPTIONAL:
    print("=== no API drift detected ===")
