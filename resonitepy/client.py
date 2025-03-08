"""
This module defines the Resonite client, which interacts with the Resonite API.
"""

import os
import dataclasses
import json
import logging
from datetime import datetime
from hashlib import sha256
from os import path as OSpath
from typing import Dict, List
from urllib.parse import ParseResult, urlparse

import dacite
from requests import Session
from requests import exceptions as requests_exceptions
from dateutil.parser import isoparse

from . import __version__
from .classes import (
    LoginDetails,
    ResoniteDirectory,
    ResoniteContact,
    ResoniteLink,
    ResoniteRecord,
    ResoniteUser,
    supporterMetadataTypeMapping,
    resoniteUserEntitlementTypeMapping,
    ResoniteUserEntitlementShoutOut,
    ResoniteUserEntitlementCredits,
    ResoniteMessage,
    ResoniteMessageType,
    ResoniteMessageContentSessionInvite,
    ResoniteMessageContentRequestInvite,
    ResoniteMessageContentObject,
    ResoniteMessageContentSound,
    ResoniteMessageContentText,
    ResoniteCloudVar,
    RecordType,
    recordTypeMapping,
    OnlineStatus,
    ResoniteSession,
    CurrentResoniteSessionAccessLevel,
    ContactStatus,
    OwnerType,
    ResoniteCloudVarDefs,
    Platform,
    ResoniteUserMembership,
    ResoniteGroup,
    ResoniteGroupMember,
)
from .utils import getOwnerType

from .endpoints import API_URL, ASSETS_URL
from resonitepy import exceptions as resonite_exceptions

try:
    DEBUG = json.loads(os.environ.get('DEBUG', 'False').lower())
except json.decoder.JSONDecodeError:
    print("Debug must be True or False")
    exit(1)

DACITE_CONFIG = dacite.Config(
    cast=[
        ResoniteMessageType,
        RecordType,
        OnlineStatus,
        CurrentResoniteSessionAccessLevel,
        ContactStatus,
    ],
    type_hooks={
        datetime: isoparse,
        ParseResult: urlparse,
    },
    strict=DEBUG,
    strict_unions_match=DEBUG,
)

AUTHFILE_NAME = "auth.token"

def to_class(data_class: type , data: dict, config: dacite.Config) -> object:
    """ Converts a dictionary to an instance of the specified data class.

    Args:
        data_class (type): The type of the data class to convert to.
        data (dict): The dictionary containing the data to convert.
        config (dacite.Config): The Dacite configuration for the conversion.

    Returns:
        object: An instance of the specified data class.

    Raises:
        Exception: If an error occurs during the conversion.

    Example:
        >>> data = {'globalVersion': 1, 'localVersion': 2}
        >>> config = dacite.Config()
        >>> record_version = to_class(ResoniteRecordVersion, data, config)
    """
    try:
        return dacite.from_dict(data_class, data, config)
    except Exception as exc:
        print(f'Error for class {data_class.__name__}')
        if DEBUG:
            print("With data:")
            print(data)
        print(exc)

@dataclasses.dataclass
class Client:
    """ Representation of a Resonite client.

    This class provides methods for interacting with the Resonite API.

    Attributes:
        userId (str): The ID of the user associated with the client. In the Resonite `U-` format.
        token (str): The authentication token for the client.
        expire (str): The expiration date of the authentication token. (Not used by the API)
        rememberMe (bool): Whether to remember the client's session. (default: False)
        lastUpdate (datetime): The timestamp of the last update. (default: None)
        secretMachineIdHash (str): The hash of the secret machine ID. (default: None)
        secretMachineIdSalt (str): The salt of the secret machine ID. (default: None)
        session (Session): The session object used for making API requests. (default: Session())
        session.headers['UID'] (str): The UID header for the session. (default: randomly generated)

    Examples:
        >>> client = Client()
        >>> client.login(LoginDetails(username='foxxie', password='pass'))
        >>> inventory = client.getInventory()
    """
    userId: str = None
    token: str = None
    expire: datetime = None  # This don't seems to be use by the API.
    rememberMe: bool = False
    lastUpdate: datetime = None
    secretMachineIdHash: str = None
    secretMachineIdSalt: str = None
    session: Session = None

    def __init__(self):
        self.session = Session()
        self.session.headers['UID'] = sha256(os.urandom(16)).hexdigest().upper()

    @property
    def headers(self) -> dict:
        """ Returns the headers for API requests.

        Returns:
            dict: A dictionary containing the headers.

        Examples:
            >>> client = Client()
            >>> headers = client.headers
        """
        default = {"User-Agent": f"resonitepy/{__version__}"}
        if not self.userId or not self.token:
            logging.warning("WARNING: headers sections not set. this might throw an error soon...")
            return default
        default["Authorization"] = f"res {self.userId}:{self.token}"
        return default

    @staticmethod
    def processRecordList(data: List[dict]) -> [ResoniteRecord]:
        """ Processes a list of raw records and returns a list of ResoniteRecord objects.

        Args:
            data: A list of dictionaries representing the raw records.

        Returns:
            A list of ResoniteRecord objects.
        """
        ret = []
        for raw_item in data:
            item = to_class(ResoniteRecord, raw_item, DACITE_CONFIG)
            x = to_class(recordTypeMapping[item.recordType], raw_item, DACITE_CONFIG)
            ret.append(x)
        return ret

    def request(
            self, verb: str, path: str, data: dict = None, json: dict = None,
            params: dict = None, ignoreUpdate: bool = False
        ) -> Dict:
        """ Sends an API request and returns the response.

        While the API dont seems to implement more security, the official client
        behavior is respected. For now it will only disconnect after 1 day of
        inactivity.

        Args:
            verb (str): The HTTP verb for the request.
            path (str): The path of the API endpoint.
            data (str): The data to send in the request body. (default: None)
            json (dict): The JSON data to send in the request body. (default: None)
            params (dict): The query parameters for the request. (default: None)
            ignoreUpdate (bool): Whether to ignore the update check. (default: False)

        Returns:
            Dict: The response from the API.

        Raises:
            resonite_exceptions.InvalidCredentials: If the credentials are invalid.
            resonite_exceptions.InvalidToken: If the token is invalid.
            resonite_exceptions.ResoniteAPIException: If an API error occurs.

        Example:
            >>> client = Client()
            >>> response = client.request('get', '/users/U-foxxie')
        """
        if self.lastUpdate and not ignoreUpdate:
            lastUpdate = self.lastUpdate
            # From PolyLogix/CloudX.js, the token seems to expire after 3600000 seconds
            if (datetime.now() - lastUpdate).total_seconds() <= 3600000:
                self.request('patch', '/userSessions', ignoreUpdate=True)
                self.lastUpdate = datetime.now()
            # While the API dont seems to implement more security, official client behavior must be respected.
            # Only disconnect after 1 day of inactivity for now.
            # TODO: Implement disconnection after 1 week of inactivity when implementing the rememberMe feature.
            #if 64800 >= (datetime.now() - lastUpdate).total_seconds() >= 85536:
            #    self.request('patch', '/userSessions', ignoreUpdate=True)
            else:
                raise resonite_exceptions.InvalidToken("Token expired")
        args = {'url': API_URL + path}
        if data: args['data'] = data
        if json: args['json'] = json
        if params: args['params'] = params
        func = getattr(self.session, verb, None)
        with func(**args) as req:
            logging.debug("ResoniteAPI: [{}] {}".format(req.status_code, args))
            if req.status_code not in [200, 204]:
                if "Invalid credentials" in req.text:
                    raise resonite_exceptions.InvalidCredentials(req.text)
                elif req.status_code == 403:
                    raise resonite_exceptions.InvalidToken(req.headers)
                else:
                    raise resonite_exceptions.ResoniteAPIException(req)
            if req.status_code == 200:
                try:
                    response = req.json()
                    if "message" in response:
                        raise resonite_exceptions.ResoniteAPIException(req, message=response["message"])
                    return response
                except requests_exceptions.JSONDecodeError:
                    return req.text
            # In case of a 204 response
            return

    def login(self, data: LoginDetails) -> None:
        """ Logs in the client with the provided login details.

        Args:
            data (LoginDetails): The login details.

        Returns:
            None

        Examples:
            >>> client = Client()
            >>> login_details = LoginDetails(username='foxxie', password='pass')
            >>> client.login(login_details)
        """
        json=dataclasses.asdict(data)
        json['authentication'] = data.authentication.build_dict()
        response = self.request('post', "/userSessions", json=json)
        self.userId = response["entity"]["userId"]
        self.token = response["entity"]["token"]
        self.secretMachineIdHash = response["entity"]["secretMachineIdHash"]
        self.secretMachineIdSalt = response["entity"]["secretMachineIdSalt"]
        self.expire = isoparse(response["entity"]["expire"])
        self.lastUpdate = datetime.now()
        self.session.headers.update(self.headers)

    def logout(self) -> None:
        """ Logs out the client.

        Returns:
            None

        Examples:
            >>> client = Client()
            >>> client.logout()
        """
        self.request('delete',
            "/userSessions/{}/{}".format(self.userId, self.token),
            ignoreUpdate=True,
        )
        self.clean_session()

    def clean_session(self) -> None:
        """ Cleans the client's session.

        Returns:
            None

        Examples:
            >>> client = Client()
            >>> client.clean_session()
        """
        self.userId = None
        self.token = None
        self.expire = None
        self.secretMachineIdHash = None
        self.secretMachineIdSalt = None
        self.lastUpdate = None
        del self.session.headers["Authorization"]
        self.session.headers.update(self.headers)

    def load_token(self) -> None:
        """ Loads the authentication token from a file.

        Returns:
            None

        Raises:
            resonite_exceptions.NoTokenError: If the token file does not exist or the token has expired.

        Examples:
            >>> client = Client()
            >>> client.load_token()
        """
        if OSpath.exists(AUTHFILE_NAME):
            with open(AUTHFILE_NAME, "r") as f:
                session = json.load(f)
                expire = datetime.fromisoformat(session["expire"])
                if datetime.now().timestamp() < expire.timestamp():
                    self.token = session["token"]
                    self.userId = session["userId"]
                    self.expire = expire
                    self.secretMachineIdHash = session["secretMachineIdHash"]
                    self.secretMachineIdSalt = session["secretMachineIdSalt"]
                    self.session.headers.update(self.headers)
                else:
                    raise resonite_exceptions.NoTokenError
        else:
            raise resonite_exceptions.NoTokenError

    def save_token(self) -> None:
        """ Saves the authentication token to a file.

        Returns:
            None

        Examples:
            >>> client = Client()
            >>> client.save_token()
        """
        with open(AUTHFILE_NAME, "w+") as f:
            json.dump(
                {
                    "userId": self.userId,
                    "expire": self.expire.isoformat(),
                    "token": self.token,
                    "secretMachineIdHash": self.secretMachineIdHash,
                    "secretMachineIdSalt": self.secretMachineIdSalt,
                },
                f,
            )

    def resDBSignature(self, resUrl: str) -> str:
        """ Returns the Resonite DB signature from a Resonite URL.

        Args:
            resUrl (url): The Resonite URL.

        Returns:
            str: The Resonite DB signature.

        # TODO: Fix example
        Examples:
            >>> client = Client()
            >>> signature = client.resDBSignature("resrec://U-123/R-456")
        """
        return resUrl.split("//")[1].split(".")[0]

    def resDbToHttp(self, resUrl: str) -> str:
        """  Converts a Resonite URL to an HTTP URL.

        Args:
            resUrl (str): The Resonite URL.

        Returns:
            str: The HTTP URL.

        # TODO: Fix example
        Examples:
            >>> client = Client()
            >>> http_url = client.resDbToHttp("resrec://U-123/R-456")
        """
        url = ASSETS_URL + self.resDBSignature(resUrl)
        return url

    def to_resonite_user(self, data: dict) -> ResoniteUser:
        if 'entitlements' in data:
            entitlements = []
            for entitlement in data['entitlements']:
                if '$type' in entitlement:
                    entitlement_type = entitlement['$type']
                    del entitlement['$type']
                    entitlements.append(
                        to_class(
                            resoniteUserEntitlementTypeMapping[entitlement_type],
                            entitlement,
                            DACITE_CONFIG
                        )
                    )
            data['entitlements'] = entitlements
        if '2fa_login' in data:
            data['two_fa_login'] = data['2fa_login']
            del data['2fa_login']
        if 'supporterMetadata' in data:
            supporterMetadatas = []
            for supporterMetadata in data['supporterMetadata']:
                if '$type' in supporterMetadata:
                    supporterMetadata_type = supporterMetadata['$type']
                    del supporterMetadata['$type']
                    supporterMetadatas.append(
                        to_class(
                            supporterMetadataTypeMapping[supporterMetadata_type],
                            supporterMetadata,
                            DACITE_CONFIG
                        )
                    )
            data['supporterMetadata'] = supporterMetadatas
        return data

    def getUserData(self, user: str = None) -> ResoniteUser:
        """ Retrieves user data for the specified user.

        Args:
            user (str): The ID of the user to retrieve data for. If not provided, retrieves data for the client's user ID.

        Returns:
            ResoniteUser: A ResoniteUser object representing the user data.

        Examples:
            >>> client = Client()
            >>> user_data = client.getUserData()
        """
        if user is None:
            user = self.userId
        response = self.request('get', "/users/" + user)
        resonite_user = self.to_resonite_user(response)
        return to_class(ResoniteUser, resonite_user, DACITE_CONFIG)

    def getMemberships(self) -> List[ResoniteUserMembership]:
        """ Retrieve current connected user group memberships.

        Return
            List[ResoniteUserMembership]: The list of groups where the user is a member.

        """
        response = self.request('get', f'/users/{self.userId}/Memberships')
        return [to_class(ResoniteUserMembership, group, DACITE_CONFIG) for group in response]

    def getGroup(self, groupId: str) -> ResoniteGroup:
        """ Retrieve group information.

        Args:
            groupId (str): The group name starting with G-

        Returns:
            ResoniteGroup: An object with the group information.
        """
        response = self.request('get', f'/groups/{groupId}')
        return to_class(ResoniteGroup, response, DACITE_CONFIG)

    def getGroupMembers(self, groupId: str) -> List[ResoniteGroupMember]:
        """ Retrieve members from a group.

        Args:
            groupId (str): The group name starting with G-

        Returns:
            List[ResoniteGroupMember]: A list with the group members.
        """
        response = self.request('get', f'/groups/{groupId}/members')
        return [to_class(ResoniteGroupMember, group_member, DACITE_CONFIG) for group_member in response]

    def getGroupMember(self, groupId: str, userId: str) -> ResoniteGroupMember:
        """ Retrieve a member from a group.

        Args:
            groupId (str): The group name starting with G-
            userId (str): The username starting with U-
        Returns:
            ResoniteGroupMember: An object with the member information.
        """
        response = self.request('get', f'/groups/{groupId}/members/{userId}')
        return to_class(ResoniteGroupMember, response, DACITE_CONFIG)

    def getSessions(
        self,
        compatibilityHash: str = None,
        name: str = None,
        universeId: str = None,
        hostName: str = None,
        hostId: str = None,
        minActiveUsers: int = 0,
        includeEmptyHeadless: bool = True,
    ) -> List[ResoniteSession]:
        """ Retrieves all active Resonite session.

        Args:
            compatibilityHash (str): The compatibility-hash sessions needs to have. A Resonite client can only join a session if this hash matches between client and server.
            name (str): The name of the session to search for.
            universeId (str): The id of the universe sessions need to be part of.
            hostName (str): The name of the user currently hosting the session.
            hostId (str): The id of the user currently hosting the session.
            minActiveUsers (int): he minimum amount of active users a session need to have. (default: 0)
            includeEmptyHeadless: (bool): Should empty headless servers be included in the results. (Default: True)

        Returns:
            List[ResoniteSession]: A list of ResoniteSessions

        Examples:
            >>> client = Client()
            >>> client.getSession()
        """
        response = self.request('get', '/sessions')
        return [to_class(ResoniteSession, session, DACITE_CONFIG) for session in response]

    def getSession(self, session_id: str) -> ResoniteSession:
        """ Retrieves session information for the specified session ID.

        Args:
            session_id (str): The ID of the session.

        Returns:
            ResoniteSession: A ResoniteSession object representing the session information.

        Examples:
            >>> client = Client()
            >>> session = client.getSession('12345')
        """
        response = self.request('get', f'/sessions/{session_id}')
        return to_class(ResoniteSession, response, DACITE_CONFIG)

    def getContacts(self) -> List[ResoniteContact]:
        """ Retrieves the contacts of the client.

        Returns:
            List[ResoniteContact]: A list of ResoniteContact objects representing the contacts.

        Examples:
            >>> client = Client()
            >>> contacts = client.getContacts()
        """
        response = self.request('get', f"/users/{self.userId}/contacts")
        return [to_class(ResoniteContact, user, DACITE_CONFIG) for user in response]

    def getInventory(self) -> List[ResoniteRecord]:
        """ Retrieves the inventory of the user.

        Returns:
            List[ResoniteRecord]: A list of ResoniteRecord objects representing the inventory.

        Examples:
            >>> client = Client()
            >>> inventory = client.getInventory()
        """
        response = self.request(
            'get',
            f"/users/{self.userId}/records",
            params={"path": "Inventory"},
        )
        return self.processRecordList(response)

    def getDirectory(self, directory: ResoniteDirectory) -> List[ResoniteRecord]:
        """ Retrieves the contents of a directory.

        Args:
            directory (ResoniteDirectory): The ResoniteDirectory object representing the directory.

        Returns:
            List[ResoniteRecord]: A list of ResoniteRecord objects representing the contents of the directory.

        Examples:
            >>> client = Client()
            >>> directory = ResoniteDirectory(ownerId='U-123', content_path='path/to/directory')
            >>> contents = client.getDirectory(directory)
        """
        response = self.request(
            'get',
            f"/users/{directory.ownerId}/records",
            params={"path": directory.content_path},
        )
        return self.processRecordList(response)

    def resolveLink(self, link: ResoniteLink) -> ResoniteDirectory:
        """ Resolves a link type record and returns its directory.

        Args:
            link (ResoniteLink): The ResoniteLink object representing the link type record.

        Returns:
            ResoniteDirectory: A ResoniteDirectory object representing the directory.

        Raises:
            resonite_exceptions.ResoniteException: If the link type is not supported.

        Examples:
            >>> client = Client()
            >>> link = ResoniteLink(assetUri='resrec://U-123/R-456')
            >>> directory = client.resolveLink(link)
        """
        if link.assetUri.scheme != 'resrec':
            raise resonite_exceptions.ResoniteException(f'Not supported link type {link}')
        import re
        # TODO: Add support for special resonite folder in format: `/G-Resonite/Inventory/Resonite Essential`
        m = re.search('\/(U-.*)\/(R-.*)', link.assetUri.path)
        if not m:
            raise resonite_exceptions.ResoniteException(f'Not supported link type {link}')
        user = m.group(1)
        record = m.group(2)
        response = self.request(
            'get',
            f"/users/{user}/records/{record}",
        )
        return to_class(ResoniteDirectory, response, DACITE_CONFIG)


    def getMessageLegacy(
        self, fromTime: str = None, maxItems: int = 100,
        user: str = None, unreadOnly: bool = False
    ) -> List[ResoniteMessage]:
        """ Retrieves a list of Resonite messages.

        This API endpoint should be understand as deprecated. Please use the SignalR
        protocol for this instead.

        Args:
            fromTime (str): The starting time to retrieve messages from. (default: None, Not yet implemented)
            maxItems (int): The maximum number of messages to retrieve. (default: 100)
            user (str): The user ID to filter messages by. (default: None)
            unreadOnly (bool): Whether to retrieve only unread messages. (default: False)

        Returns:
            A list of ResoniteMessage objects.

        Raises:
            ValueError: If fromTime is provided (not yet implemented).

        Examples:
            >>> client = ResoniteClient()
            >>> messages = client.getMessageLegacy(maxItems=50, unreadOnly=True)
        """
        params = {}
        if fromTime:
            raise ValueError('fromTime is not yet implemented')
        params['maxItems'] = maxItems
        params['unreadOnly'] = unreadOnly
        if user:
            params['user'] = user
        response = self.request(
            'get',
            f'/users/{self.userId}/messages',
            params=params
        )
        messages = []
        for message in response:
            if message['messageType'] == 'SessionInvite':
                message['content'] = json.loads(message['content'])
                ResoniteMessageContentType = ResoniteMessageContentSessionInvite
            elif message['messageType'] == 'InviteRequest':
                message['content'] = json.loads(message['content'])
                ResoniteMessageContentType = ResoniteMessageContentRequestInvite
            elif message['messageType'] == 'Object':
                message['content'] = json.loads(message['content'])
                ResoniteMessageContentType = ResoniteMessageContentObject
            elif message['messageType'] == 'Sound':
                message['content'] = json.loads(message['content'])
                ResoniteMessageContentType = ResoniteMessageContentSound
            elif  message['messageType'] == 'Text':
                ResoniteMessageContentType = ResoniteMessageContentText
                message['content'] = {'content': message['content']}
            else:
                raise ValueError(f'Non supported type {message["messageType"]}')
            message['content'] = to_class(
                ResoniteMessageContentType, message['content'], DACITE_CONFIG
            )
            messages.append(
                to_class(ResoniteMessage, message, DACITE_CONFIG)
            )
        return messages

    def getOwnerPath(self, ownerId: str) -> str:
        """ Returns the owner path based on the owner ID.

        Args:
            ownerId (str): The ID of the owner.

        Returns:
            str: The owner path.

        Raises:
            ValueError: If the owner type is invalid.

        Examples:
            >>> client = Client()
            >>> owner_path = client.getOwnerPath('U-123')
        """
        ownerType = getOwnerType(ownerId)
        if ownerType == OwnerType.USER:
            return "users"
        elif ownerType == OwnerType.GROUP:
            return "groups"
        else:
            raise ValueError(f"invalid ownerType for {ownerId}")

    def listCloudVar(self, ownerId: str) -> List[ResoniteCloudVar]:
        """ Lists the cloud variables for the specified owner.

        Args:
            ownerId (str): The ID of the owner.

        Returns:
            List[ResoniteCloudVar]: A list of ResoniteCloudVar objects representing the cloud variables.

        Examples:
            >>> client = Client()
            >>> cloud_vars = client.listCloudVar('U-123')
        """
        response = self.request(
            'get',
            f'/{self.getOwnerPath(ownerId)}/{ownerId}/vars'
        )
        return [to_class(ResoniteCloudVar, cloud_var, DACITE_CONFIG) for cloud_var in response]

    def getCloudVar(self, ownerId: str, path: str) -> ResoniteCloudVar:
        """ Retrieves a cloud variable for the specified owner and path.

        Args:
            ownerId (str): The ID of the owner.
            path (str): The path of the cloud variable.

        Returns:
            ResoniteCloudVar: A ResoniteCloudVar object representing the cloud variable.

        Examples:
            >>> client = Client()
            >>> cloud_var = client.getCloudVar('U-123', 'path/to/cloudvar')
        """
        response = self.request(
            'get',
            f'/{self.getOwnerPath(ownerId)}/{ownerId}/vars/{path}'
        )
        return to_class(ResoniteCloudVar, response, DACITE_CONFIG)

    def getCloudVarDefs(self, ownerId: str, path: str) -> ResoniteCloudVarDefs:
        """ Retrieves the cloud variable definitions for the specified owner and path.

        Args:
            ownerId (str): The ID of the owner.
            path (str): The path of the cloud variable.

        Returns:
            ResoniteCloudVarDefs: A ResoniteCloudVarDefs object representing the cloud variable definitions.

        Raises:
            resonite_exceptions.ResoniteException: If the cloud variable doesn't exist.

        Examples:
            >>> client = Client()
            >>> defs = client.getCloudVarDefs('U-123', 'path/to/cloudvar')
        """
        json=[{
            "ownerId": ownerId,
            "path": path,
        }]
        response = self.request(
            'post',
            f'/readvars',
            json=json,
        )
        if not response:
            raise resonite_exceptions.ResoniteException(f"{ownerId} {path} doesn't exist")
        return to_class(ResoniteCloudVarDefs, response[0]['definition'], DACITE_CONFIG)

    def setCloudVar(self, ownerId: str, path: str, value: str) -> None:
        """ Sets the value of a cloud variable for the specified owner and path.

        Args:
            ownerId (str): The ID of the owner.
            path (str): The path of the cloud variable.
            value (str): The value to set for the cloud variable.

        Returns:
            None

        Examples:
            >>> client = Client()
            >>> client.setCloudVar('U-123', 'path/to/cloudvar', 'new value')
        """
        return self.request(
            'put',
            f'/{self.getOwnerPath(ownerId)}/{ownerId}/vars/{path}',
            json = {
                "ownerId": ownerId,
                "path": path,
                "value": value,
            }
        )

    def searchUser(self, username: str) -> List[ResoniteUser]:
        """ Searches for users based on username.

        This is not the U- Resonite user id, the API will search over usernames not ids.

        Args:
            username (str): The username to search for.

        Returns:
            List[ResoniteUser]: A list of ResoniteUser objects matching the search criteria.

        Examples:
            >>> client = Client()
            >>> users = client.searchUser('foxxie')
        """
        #TODO: the entitlements part could be optimized!
        response = self.request(
            'get',
            '/users',
            params = {'name': username}
        )
        users = []
        for user in response:
            users.append(to_class(ResoniteUser, self.to_resonite_user(user), DACITE_CONFIG))
        return users

    def getUser(self, userId: str) -> ResoniteUser:
        """ Retrieve user directly.

        Args:
            userId (int): Ther username starting with U-

        Returns:
            ResoniteUser: The user
        """
        response = self.request('get', f'/users/{userId}')
        return to_class(ResoniteUser, self.to_resonite_user(response), DACITE_CONFIG)

    def getUserByName(self, userId) -> ResoniteUser:
        reponse = self.request('get', f'/users/{userId}?byUsername=True')
        return to_class(ResoniteUser, self.to_resonite_user(reponse), DACITE_CONFIG)

    def platform(self) -> Platform:
        """ Return information about the platform.
        """
        response = self.request('get', '/platform')
        return to_class(Platform, response, DACITE_CONFIG)