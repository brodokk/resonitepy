"""
This module define the client who will do the request to the
Resonite API.
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
    ResoniteUserEntitlementShoutOut,
    ResoniteUserEntitlementCredits,
    ResoniteMessage,
    ResoniteMessageType,
    ResoniteMessageContentSessionInvite,
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
)
from .utils import (
    nested_asdict_factory,
    getOwnerType,
)

from .endpoints import API_URL, ASSETS_URL
from resonitepy import exceptions as resonite_exceptions

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
)

AUTHFILE_NAME = "auth.token"


@dataclasses.dataclass
class Client:
    """Representation of a resonitepy Resonite client."""
    userId: str = None
    token: str = None
    expire: datetime = None  # This don't seems to be use by the API.
    rememberMe: bool = False
    lastUpdate: datetime = None
    secretMachineIdHash: str = None
    secretMachineIdSalt: str = None
    session: Session = Session()
    session.headers['UID'] = sha256(os.urandom(16)).hexdigest().upper()

    @property
    def headers(self) -> dict:
        default = {"User-Agent": f"resonitepy/{__version__}"}
        if not self.userId or not self.token:
            logging.warning("WARNING: headers sections not set. this might throw an error soon...")
            return default
        default["Authorization"] = f"res {self.userId}:{self.token}"
        return default

    @staticmethod
    def processRecordList(data: List[dict]):
        ret = []
        for raw_item in data:
            item = dacite.from_dict(ResoniteRecord, raw_item, DACITE_CONFIG)
            x = dacite.from_dict(recordTypeMapping[item.recordType], raw_item, DACITE_CONFIG)
            ret.append(x)
        return ret

    def _request(
            self, verb: str, path: str, data: dict = None, json: dict = None,
            params: dict = None, ignoreUpdate: bool = False
        ) -> Dict:
        if self.lastUpdate and not ignoreUpdate:
            lastUpdate = self.lastUpdate
            # From PolyLogix/CloudX.js, the token seems to expire after 3600000 seconds
            if (datetime.now() - lastUpdate).total_seconds() <= 3600000:
                self._request('patch', '/userSessions', ignoreUpdate=True)
                self.lastUpdate = datetime.now()
            # While the API dont seems to implement more security, official client behavior must be respected.
            # Only disconnect after 1 day of inactivity for now.
            # TODO: Implement disconnection after 1 week of inactivity when implementing the rememberMe feature.
            #if 64800 >= (datetime.now() - lastUpdate).total_seconds() >= 85536:
            #    self._request('patch', '/userSessions', ignoreUpdate=True)
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
        json=dataclasses.asdict(data)
        json['authentication'] = data.authentication.build_dict()
        response = self._request('post', "/userSessions", json=json)
        self.userId = response["entity"]["userId"]
        self.token = response["entity"]["token"]
        self.secretMachineIdHash = response["entity"]["secretMachineIdHash"]
        self.secretMachineIdSalt = response["entity"]["secretMachineIdSalt"]
        self.expire = isoparse(response["entity"]["expire"])
        self.lastUpdate = datetime.now()
        self.session.headers.update(self.headers)

    def logout(self) -> None:
        self._request('delete',
            "/userSessions/{}/{}".format(self.userId, self.token),
            ignoreUpdate=True,
        )
        self.clean_session()

    def clean_session(self) -> None:
        self.userId = None
        self.token = None
        self.expire = None
        self.secretMachineIdHash = None
        self.secretMachineIdSalt = None
        self.lastUpdate = None
        del self.session.headers["Authorization"]
        self.session.headers.update(self.headers)

    def load_token(self):
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

    def save_token(self):
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
        return resUrl.split("//")[1].split(".")[0]

    def resDbToHttp(self, resUrl: str) -> str:
        url = ASSETS_URL + self.resDBSignature(resUrl)
        return url

    def getUserData(self, user: str = None) -> ResoniteUser:
        if user is None:
            user = self.userId
        response = self._request('get', "/users/" + user)
        return dacite.from_dict(ResoniteUser, response, DACITE_CONFIG)

    def getSession(self, session_id: str) -> ResoniteSession:
        """ Return session information.
        """
        response = self._request('get', f'/sessions/{session_id}')
        return dacite.from_dict(ResoniteSession, response, DACITE_CONFIG)

    def getContacts(self):
        """
        returns the contacts you have.

        Note: does not create contact out of thin air. you need to do that yourself.
        """
        response = self._request('get', f"/users/{self.userId}/contacts")
        return [dacite.from_dict(ResoniteContact, user, DACITE_CONFIG) for user in response]

    def getInventory(self) -> List[ResoniteRecord]:
        """
        The typical entrypoint to the inventory system.
        """
        response = self._request(
            'get',
            f"/users/{self.userId}/records",
            params={"path": "Inventory"},
        )
        return self.processRecordList(response)

    def getDirectory(self, directory: ResoniteDirectory) -> List[ResoniteRecord]:
        """
        given a directory, return it's contents.
        """
        response = self._request(
            'get',
            f"/users/{directory.ownerId}/records",
            params={"path": directory.content_path},
        )
        return self.processRecordList(response)

    def resolveLink(self, link: ResoniteLink) -> ResoniteDirectory:
        """
        given a link type record, will return it's directory. directoy can be passed to getDirectory
        """
        if link.assetUri.scheme != 'resrec':
            raise resonite_exceptions.ResoniteException(f'Not supported link type {link}')
        import re
        m = re.search('\/(U-.*)\/(R-.*)', link.assetUri.path)
        if not m:
            raise resonite_exceptions.ResoniteException(f'Not supported link type {link}')
        user = m.group(1)
        record = m.group(2)
        response = self._request(
            'get',
            f"/users/{user}/records/{record}",
        )
        return dacite.from_dict(ResoniteDirectory, response, DACITE_CONFIG)


    def getMessageLegacy(
        self, fromTime: str = None, maxItems: int = 100,
        user: str = None, unreadOnly: bool = False
    ) -> List[ResoniteMessage]:
        params = {}
        if fromTime:
            raise ValueError('fromTime is not yet implemented')
        params['maxItems'] = maxItems
        params['unreadOnly'] = unreadOnly
        if user:
            params['user'] = user
        response = self._request(
            'get',
            f'/users/{self.userId}/messages',
            params=params
        )
        messages = []
        for message in response:
            if message['messageType'] == 'SessionInvite':
                message['content'] = json.loads(message['content'])
                ResoniteMessageContentType = ResoniteMessageContentSessionInvite
            elif message['messageType'] == 'Object':
                message['content'] = json.loads(message['content'])
                ResoniteMessageContentType = ResoniteMessageContentObject
            elif message['messageType'] == 'Sound':
                message['content'] = json.loads(message['content'])
                ResoniteMessageContentType = ResoniteMessageContentSound
            elif  message['messageType'] == 'Text':
                ResoniteMessageContentType = ResoniteMessageContentText
            else:
                raise ValueError(f'Non supported type {message["messageType"]}')
            message['content'] = dacite.from_dict(
                ResoniteMessageContentType, message['content'], DACITE_CONFIG
            )
            messages.append(
                dacite.from_dict(ResoniteMessage, message, DACITE_CONFIG)
            )
        return messages

    def getOwnerPath(self, ownerId: str) -> str:
        ownerType = getOwnerType(ownerId)
        if ownerType == OwnerType.USER:
            return "users"
        elif ownerType == OwnerType.GROUP:
            return "groups"
        else:
            raise ValueError(f"invalid ownerType for {ownerId}")

    def listCloudVar(self, ownerId: str) -> List[ResoniteCloudVar]:
        response = self._request(
            'get',
            f'/{self.getOwnerPath(ownerId)}/{ownerId}/vars'
        )
        return [dacite.from_dict(ResoniteCloudVar, cloud_var, DACITE_CONFIG) for cloud_var in response]

    def getCloudVar(self, ownerId: str, path: str) -> ResoniteCloudVar:
        response = self._request(
            'get',
            f'/{self.getOwnerPath(ownerId)}/{ownerId}/vars/{path}'
        )
        return dacite.from_dict(ResoniteCloudVar, response, DACITE_CONFIG)

    def getCloudVarDefs(self, ownerId: str, path: str) -> ResoniteCloudVarDefs:
        json=[{
            "ownerId": ownerId,
            "path": path,
        }]
        response = self._request(
            'post',
            f'/readvars',
            json=json,
        )
        if not response:
            raise resonite_exceptions.ResoniteException(f"{ownerId} {path} doesn't exist")
        return dacite.from_dict(ResoniteCloudVarDefs, response[0]['definition'], DACITE_CONFIG)

    def setCloudVar(self, ownerId: str, path: str, value: str) -> None:
        return self._request(
            'put',
            f'/{self.getOwnerPath(ownerId)}/{ownerId}/vars/{path}',
            json = {
                "ownerId": ownerId,
                "path": path,
                "value": value,
            }
        )

    def searchUser(self, username: str) -> List[ResoniteUser]:
        """
        return a list of user based on username.

        This is not the U- Resonite user id, the API will search over usernames not ids.
        """
        response = self._request(
            'get',
            '/users',
            params = {'name': username}
        )
        users = []
        for user in response:
            if 'entitlements' in user:
                entitlements = []
                for entitlement in user['entitlements']:
                    if entitlement['$type'] == 'shoutOut':
                        del entitlement['$type']
                        entitlements.append(
                            ResoniteUserEntitlementShoutOut(**entitlement)
                        )
                    elif entitlement['$type'] == 'credits':
                        del entitlement['$type']
                        entitlements.append(
                            ResoniteUserEntitlementCredits(**entitlement)
                        )
                    else:
                        print('Warning: {entitlement["$type"]} unknown')
                user['entitlements'] = entitlements
            users.append(dacite.from_dict(ResoniteUser, user, DACITE_CONFIG))
        return users
