import dataclasses
from datetime import datetime
import json
from os import path as OSpath
from typing import Dict, List
from urllib.parse import urlparse
import dacite
from aiohttp import ClientSession

from dateutil.parser import isoparse

from .classes import NeosDirectory, NeosLink, NeosRecord, NoTokenError, RecordType, typeMapping, LoginDetails, NeosUser

from .endpoints import CLOUDX_NEOS_API


DACITE_CONFIG = dacite.Config(
    cast=[RecordType],
    type_hooks={
        datetime: isoparse,
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
        return {"Authorization": f"neos {self.userId}:{self.token}"}

    @property
    def inventoryRoot(self) -> NeosDirectory:
        return NeosDirectory()

    @staticmethod
    def processRecordList(data: List[dict]):
        ret = []
        for raw_item in data:
            item = dacite.from_dict(NeosRecord, raw_item, DACITE_CONFIG)
            ret.append(dacite.from_dict(typeMapping[item.recordType], raw_item, DACITE_CONFIG))
        return ret

    async def login(self, data: LoginDetails) -> None:
        async with ClientSession() as session:
            async with session.post(CLOUDX_NEOS_API + "/userSessions", json=dataclasses.asdict(data)) as req:
                responce = await req.json()
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

    async def getUserData(self, user=None) -> Dict:
        if user is None:
            user = self.userId
        async with ClientSession(headers=self.headers) as session:
            async with session.get(CLOUDX_NEOS_API + "/users/" + user) as req:
                responce = await req.json()
                if "message" in responce:
                    raise ValueError(responce["message"])
                req.raise_for_status()
                return dacite.from_dict(NeosUser, await req.json(), DACITE_CONFIG)

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
            async with session.get(
                f"{CLOUDX_NEOS_API}/users/{link.ownerId}/{link.id}",
            ) as req:
                req.raise_for_status()
                return dacite.from_dict(NeosDirectory, await req.json(), DACITE_CONFIG)
