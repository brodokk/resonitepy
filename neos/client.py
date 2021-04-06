import dataclasses
import json
from datetime import datetime
from os import path as OSpath
from typing import Dict, List
from urllib.parse import ParseResult, urlparse

import dacite
from aiohttp import ClientSession, ContentTypeError
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
    typeMapping,
)
from .endpoints import CLOUDX_NEOS_API
from .exceptions import NoTokenError
from neos import exceptions

DACITE_CONFIG = dacite.Config(
    cast=[RecordType],
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
    expirey: datetime = None
    secretMachineId: str = None

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
            x = dacite.from_dict(typeMapping[item.recordType], raw_item, DACITE_CONFIG)
            ret.append(x)
        return ret

    async def login(self, data: LoginDetails) -> None:
        async with ClientSession() as session:
            async with session.post(CLOUDX_NEOS_API + "/userSessions", json=dataclasses.asdict(data)) as req:
                try:
                    responce = await req.json()
                except ContentTypeError:
                    raise ValueError(await req.text())
                if "message" in responce:
                    raise ValueError(responce["message"])
                req.raise_for_status()
                self.userId = responce["userId"]
                self.token = responce["token"]
                self.secretMachineId = responce["secretMachineId"]
                self.expirey = isoparse(responce["expire"])

    def loadToken(self):
        if OSpath.exists(AUTHFILE_NAME):
            with open(AUTHFILE_NAME, "r") as f:
                session = json.load(f)
                expirey = datetime.fromisoformat(session["expire"])
                if datetime.now().timestamp() < expirey.timestamp():
                    print("reading token from disk")
                    self.token = session["token"]
                    self.userId = session["userId"]
                    self.expirey = expirey
                    self.secretMachineId = session["secretMachineId"]
                else:
                    raise NoTokenError
        else:
            raise NoTokenError

    def saveToken(self):
        with open(AUTHFILE_NAME, "w+") as f:
            json.dump(
                {
                    "userId": self.userId,
                    "expire": self.expirey.isoformat(),
                    "token": self.token,
                    "secretMachineId": self.secretMachineId,
                },
                f,
            )

    async def getUserData(self, user: str = None) -> NeosUser:
        if user is None:
            user = self.userId
        async with ClientSession(headers=self.headers) as session:
            async with session.get(CLOUDX_NEOS_API + "/users/" + user) as req:
                responce = await req.json()
                if "message" in responce:
                    raise ValueError(responce["message"])
                req.raise_for_status()
                return dacite.from_dict(NeosUser, await req.json(), DACITE_CONFIG)

    async def getFriends(self):
        """
        returns the friends you have.

        Note: does not create friends out of thin air. you need to do that yourself.
        """
        async with ClientSession(headers=self.headers) as session:
            async with session.get(f"{CLOUDX_NEOS_API}/users/{self.userId}/friends") as req:
                responce = await req.json()
                if "message" in responce:
                    raise ValueError(responce["message"])
                req.raise_for_status()
                print(responce)
                return [dacite.from_dict(NeosFriend, user, DACITE_CONFIG) for user in responce]

    async def getInventory(self) -> List[NeosRecord]:
        """
        The typical entrypoint to the inventory system.
        """
        async with ClientSession(headers=self.headers) as session:
            async with session.get(
                f"{CLOUDX_NEOS_API}/users/{self.userId}/records",
                params={"path": "Inventory"},
            ) as req:
                req.raise_for_status()
                return self.processRecordList(await req.json())

    async def getDirectory(self, directory: NeosDirectory) -> List[NeosRecord]:
        """
        given a directory, return it's contents.
        """
        async with ClientSession(headers=self.headers) as session:
            async with session.get(
                f"{CLOUDX_NEOS_API}/users/{directory.ownerId}/records",
                params={"path": directory.content_path},
            ) as req:
                req.raise_for_status()
                return self.processRecordList(await req.json())

    async def resolveLink(self, link: NeosLink) -> NeosDirectory:
        """
        given a link type record, will return it's directory. directoy can be passed to getDirectory
        """
        async with ClientSession(headers=self.headers) as session:
            _, user, record = link.assetUri.path.split("/")  # TODO: better
            async with session.get(
                f"{CLOUDX_NEOS_API}/users/{user}/records/{record}",
            ) as req:
                try:
                    req.raise_for_status()
                except Exception as e:
                    raise exceptions.FolderNotFound(**e)

                return dacite.from_dict(NeosDirectory, await req.json(), DACITE_CONFIG)
