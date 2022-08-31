import dataclasses
import json
import logging
from datetime import datetime
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
    NeosDirectory,
    NeosFriend,
    NeosLink,
    NeosRecord,
    NeosUser,
    RecordType,
    recordTypeMapping,
    OnlineStatus,
    CurrentSessionAccessLevel,
    FriendStatus,
)
from .endpoints import CLOUDX_NEOS_API
from neos import exceptions as neos_exceptions

DACITE_CONFIG = dacite.Config(
    cast=[RecordType, OnlineStatus, CurrentSessionAccessLevel, FriendStatus],
    type_hooks={
        datetime: isoparse,
        ParseResult: urlparse,
    },
)

AUTHFILE_NAME = "auth.token"


@dataclasses.dataclass
class Client:
    userId: str = None
    token: str = None
    expire: datetime = None  # This don't seems to be use by the API.
    rememberMe: bool = False
    lastUpdate: datetime = None
    secretMachineId: str = None
    session: Session = Session()


    @property
    def headers(self) -> dict:
        default = {"User-Agent": "neos.py/{__version__}"}
        if not self.userId or not self.token:
            print("WARNING: headers sections not set. this might throw an error soon...")
            return default
        default["Authorization"] = f"neos {self.userId}:{self.token}"
        return default

    @staticmethod
    def processRecordList(data: List[dict]):
        ret = []
        for raw_item in data:
            item = dacite.from_dict(NeosRecord, raw_item, DACITE_CONFIG)
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
            if (datetime.now() - lastUpdate).total_seconds() >= 3600000:
                self._request('patch', '/userSessions', ignoreUpdate=True)
            # While the API dont seems to implement more security, official client behavior must be respected.
            # Only disconnect after 1 day of inactivity for now.
            # TODO: Implement disconnection after 1 week of inactivity when implementing the rememberMe feature.
            if 64800 >= (datetime.now() - lastUpdate).total_seconds() >= 85536:
                self._request('patch', '/userSessions', ignoreUpdate=True)
            elif (datetime.now() - lastUpdate).total_seconds() >= 86400:
                raise neos_exceptions.InvalidToken("Token expired")
        args = {'url': CLOUDX_NEOS_API + path}
        if data: args['data'] = data
        if json: args['json'] = json
        if params: args['params'] = params
        func = getattr(self.session, verb, None)
        with func(**args) as req:
            logging.debug("NeosAPI: [{}] {}".format(req.status_code, args))
            if req.status_code not in [200, 204]:
                if "Invalid credentials" in req.text:
                    raise neos_exceptions.InvalidCredentials(req.text)
                elif req.status_code == 403:
                    raise neos_exceptions.InvalidToken(req.headers)
                else:
                    raise neos_exceptions.NeosAPIException(req.status_code, req.text)
            if req.status_code == 200:
                try:
                    responce = req.json()
                    if "message" in responce:
                        raise neos_exceptions.NeosAPIException(responce["message"])
                    return responce
                except requests_exceptions.JSONDecodeError:
                    return req.text
            # In case of a 204 responce
            return

    def login(self, data: LoginDetails) -> None:
        responce = self._request('post', "/userSessions",
            json=dataclasses.asdict(data))
        self.userId = responce["userId"]
        self.token = responce["token"]
        self.secretMachineId = responce["secretMachineId"]
        self.expire = isoparse(responce["expire"])
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
        self.secretMachineId = None
        self.lastUpdate = None
        del self.session.headers["Authorization"]
        self.session.headers.update(self.headers)

    def loadToken(self):
        if OSpath.exists(AUTHFILE_NAME):
            with open(AUTHFILE_NAME, "r") as f:
                session = json.load(f)
                expire = datetime.fromisoformat(session["expire"])
                if datetime.now().timestamp() < expire.timestamp():
                    self.token = session["token"]
                    self.userId = session["userId"]
                    self.expire = expire
                    self.secretMachineId = session["secretMachineId"]
                    self.session.headers.update(self.headers)
                else:
                    raise neos_exceptions.NoTokenError
        else:
            raise neos_exceptions.NoTokenError

    def saveToken(self):
        with open(AUTHFILE_NAME, "w+") as f:
            json.dump(
                {
                    "userId": self.userId,
                    "expire": self.expire.isoformat(),
                    "token": self.token,
                    "secretMachineId": self.secretMachineId,
                },
                f,
            )

    def neosDBSignature(self, url: str) -> str:
        return url.split("//")[1].split(".")[0]

    def neosDbToHttp(self, iconUrl: str) -> str:
        url = "https://assets.neos.com/assets"
        url = url + self.neosDBSignature(iconUrl)
        return url

    def getUserData(self, user: str = None) -> NeosUser:
        if user is None:
            user = self.userId
        responce = self._request('get', "/users/" + user)
        return dacite.from_dict(NeosUser, responce, DACITE_CONFIG)

    def getFriends(self):
        """
        returns the friends you have.

        Note: does not create friends out of thin air. you need to do that yourself.
        """
        responce = self._request('get', f"/users/{self.userId}/friends")
        return [dacite.from_dict(NeosFriend, user, DACITE_CONFIG) for user in responce]

    def getInventory(self) -> List[NeosRecord]:
        """
        The typical entrypoint to the inventory system.
        """
        responce = self._request(
            'get',
            f"/users/{self.userId}/records",
            params={"path": "Inventory"},
        )
        return self.processRecordList(responce)

    def getDirectory(self, directory: NeosDirectory) -> List[NeosRecord]:
        """
        given a directory, return it's contents.
        """
        responce = self._request(
            'get',
            f"/users/{directory.ownerId}/records",
            params={"path": directory.content_path},
        )
        return self.processRecordList(responce)

    def resolveLink(self, link: NeosLink) -> NeosDirectory:
        """
        given a link type record, will return it's directory. directoy can be passed to getDirectory
        """
        _, user, record = link.assetUri.path.split("/")  # TODO: better
        responce = self._request(
            'get',
            f"/users/{user}/records/{record}",
        )
        return dacite.from_dict(NeosDirectory, responce, DACITE_CONFIG)
