"""
This module define some of the NeosVR API json
responce under usable python classes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import PureWindowsPath
from typing import List, Optional

from neosvrpy.secrets import generate
from neosvrpy.exceptions import NeosException

from urllib.parse import ParseResult


class RecordType(Enum):
    """Representation of the type of a NeosVR record."""
    OBJECT = "object"
    LINK = "link"
    DIRECTORY = "directory"
    WORLD = "world"
    TEXTURE = "texture"
    AUDIO = "audio"


@dataclass
class NeosRecord:
    """Representation of a NeosVR record."""
    id: str
    globalVersion: int
    localVersion: int
    lastModifyingUserId: Optional[str]
    name: str
    recordType: RecordType
    path: Optional[str]
    isPublic: bool
    isForPatrons: bool
    isListed: bool
    isDeleted: bool
    lastModificationTime: datetime
    visits: int
    rating: int
    ownerId: str


@dataclass
class NeosLink(NeosRecord):
    """Representation of a NeosVR link."""
    assetUri: ParseResult


@dataclass
class NeosDirectory(NeosRecord):
    """Representation of a NeosVR directory."""
    lastModifyingMachineId: Optional[str]
    ownerName: str
    tags: List[str]
    creationTime: Optional[datetime]

    @property
    def content_path(self) -> str:
        return str(PureWindowsPath(self.path, self.name))


@dataclass
class NeosObject(NeosRecord):
    """Represenation of a NeosVR object."""
    assetUri: str
    lastModifyingMachineId: str
    ownerName: str
    tags: List[str]
    creationTime: datetime

@dataclass
class NeosWorld(NeosRecord):
    """Representation of a NeosVR world."""
    pass

@dataclass
class NeosTexture(NeosRecord):
    """Representation of a NeosVR texture."""
    pass

@dataclass
class NeosAudio(NeosRecord):
    """Representation of a NeosVR audio."""
    pass


recordTypeMapping = {
    RecordType.DIRECTORY: NeosDirectory,
    RecordType.LINK: NeosLink,
    RecordType.OBJECT: NeosObject,
    RecordType.WORLD: NeosWorld,
    RecordType.TEXTURE: NeosTexture,
    RecordType.AUDIO: NeosAudio,
}


@dataclass
class LoginDetails:
    """Representation of a NeosVR login detail."""
    ownerId: Optional[str] = None
    """The ownerId of a LoginDetails should start with `U-`"""
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    secretMachineId: str = field(default_factory=generate)
    """See the generate class in the neos.secrets module."""
    rememberMe: Optional[str] = False

    def __post_init__(self):
        if not self.ownerId and not self.username and not self.email:
            raise NeosException(
                'Either an ownerId, an username or an email is needed')
        if not self.password:
            raise NeosException('A password is needed')


@dataclass
class ProfileData:
    """Representation of a NeosVR profile data."""
    iconUrl: Optional[str]
    tokenOutOut: Optional[List[str]]


@dataclass
class CreditData:
    """Representation of a NeosVR credit."""
    KFC: float
    NCR: float
    CDFT: float


@dataclass
class PatreonData:
    """Representation of a NeosVR Patreon data."""
    isPatreonSupporter: bool
    patreonId: Optional[str]
    lastPatreonPledgeCents: int
    lastTotalCents: int
    minimumTotalUnits: int
    externalCents: int
    lastExternalCents: int
    hasSupported: bool
    lastIsAnorak: bool
    priorityIssue: int
    lastPlusActivationTime: datetime
    lastActivationTime: datetime
    lastPlusPledgeAmount: int
    lastPaidPledgeAmount: int
    accountName: str
    currentAccountType: int
    currentAccountCents: int
    pledgedAccountType: int


@dataclass
class NeosUser:
    """Representation of a NeosVR user."""
    id: str
    username: str
    normalizedUsername: str
    email: Optional[str]
    registrationDate: datetime
    isVerified: bool
    quotaBytes: Optional[int]
    isLocked: bool
    accountBanExpiration: Optional[datetime]
    publicBanExpiration: Optional[datetime]
    spectatorBanExpiration: Optional[datetime]
    muteBanExpiration: Optional[datetime]
    usedBytes: Optional[int]
    profile: Optional[ProfileData]
    credits: Optional[CreditData]
    NCRdepositAddress: Optional[str]
    patreonData: Optional[PatreonData]
    tags: Optional[List[str]] = field(default_factory=list)

@dataclass
class WorldId:
    """Representation of a world id."""
    ownerId: str
    """The ownerId of a WorldId should start with `U-`"""
    recordId: str

@dataclass
class SessionUser:
    """Representation of a session user."""
    isPresent: bool
    userID: Optional[str]
    username: str

@dataclass
class Session:
    """Representation of a session."""
    activeSessions: Optional[str]
    activeUsers: int
    compatibilityHash: Optional[str]
    correspondingWorldId: Optional[WorldId]
    description: Optional[str]
    hasEnded: bool
    headlessHost: bool
    hostMachineId: str
    hostUserId: str
    hostUsername: str
    isValid: bool
    joinedUsers: int
    lastUpdate: datetime
    maxUsers: int
    mobileFriendly: bool
    name: str
    neosVersion: str
    normalizedSessionId: str
    sessionBeginTime: datetime
    sessionId: str
    sessionURLs: List[str]
    sessionUsers: List[SessionUser]
    tags: List[str]
    thumbnail: Optional[str]
    totalActiveUsers: int
    totalJoinedUsers: int


@dataclass
class PublicRSAKey:
    """Representation of a public key."""
    Exponent: str
    Modulus: str


class OnlineStatus(Enum):
    """Representation of an online status."""
    ONLINE = "Online"
    AWAY = "Away"
    BUSY = "Busy"
    OFFLINE = "Offline"


onlineStatusMapping = {
    OnlineStatus.ONLINE: "Online",
    OnlineStatus.AWAY: "Away",
    OnlineStatus.BUSY: "Busy",
    OnlineStatus.OFFLINE: "Offline",
}


class CurrentSessionAccessLevel(Enum):
    """Representation of a current session access level."""
    PRIVATE = 0
    LAN = 1
    FRIENDS = 2
    FRIENDSOFFRIENDS = 3
    REGISTEREDUSERS = 4
    ANYONE = 5

    def __str__(self):
        text = {
            'PRIVATE': 'Private',
            'LAN': 'LAN',
            'FRIENDS': 'Contacts',
            'FRIENDSOFFRIENDS': 'Contacts+',
            'REGISTEREDUSERS': 'Registered Users',
            'ANYONE': 'Anyone'
        }
        return text[self.name]


currentSessionAccessLevelMapping = {
    CurrentSessionAccessLevel.PRIVATE: 0,
    CurrentSessionAccessLevel.LAN: 1,
    CurrentSessionAccessLevel.FRIENDS: 2,
    CurrentSessionAccessLevel.FRIENDSOFFRIENDS: 3,
    CurrentSessionAccessLevel.REGISTEREDUSERS: 4,
    CurrentSessionAccessLevel.ANYONE: 5,
}


@dataclass
class UserStatusData:
    """Representation of a NeosVR user status data."""
    activeSessions: Optional[List[Session]]
    currentSession: Optional[Session]
    compatibilityHash: Optional[str]
    currentHosting: bool
    currentSessionAccessLevel: CurrentSessionAccessLevel
    currentSessionHidden: bool
    currentSessionId: Optional[str]
    isMobile: bool
    lastStatusChange: datetime
    neosVersion: Optional[str]
    onlineStatus: OnlineStatus
    OutputDevice: Optional[str]
    publicRSAKey: Optional[PublicRSAKey]

@dataclass
class NeosUserStatus:
    """Represenation of a NeosVR user status."""
    onlineStatus: OnlineStatus
    lastStatusChange: datetime
    currentSessionAccessLevel: int
    currentSessionHidden: bool
    currentHosting: bool
    compatibilityHash: Optional[str]
    neosVersion: Optional[str]
    publicRSAKey: Optional[PublicRSAKey]
    OutputDevice: Optional[str]
    isMobile: bool

class FriendStatus(Enum):
    """Representation of a FriendStatus."""
    ACCEPTED = "Accepted"
    IGNORED = "Ignored"
    REQUESTED = "Requested"
    NONE = "None"


friendStatusMapping = {
    FriendStatus.ACCEPTED: "Accepted",
    FriendStatus.IGNORED: "Ignored",
    FriendStatus.REQUESTED: "Requested",
    FriendStatus.NONE: "None",
}


@dataclass
class NeosFriend:
    """Representation of a NeosVR friend."""
    id: str
    friendUsername: str
    friendStatus: FriendStatus
    isAccepted: bool
    userStatus: UserStatusData
    profile: Optional[ProfileData]
    latestMessageTime: datetime

class NeosMessageType(Enum):
    TEXT = "Text"
    OBJECT = "Object"
    SOUND = "Sound"
    SESSIONINVITE = "SessionInvite"
    CREDITTRANSFER = "CreditTransfer"
    SUGARCUBES = "SugarCubes"

neosMessageTypeMapping = {
    NeosMessageType.TEXT: "Text",
    NeosMessageType.OBJECT: "Object",
    NeosMessageType.SOUND: "Sound",
    NeosMessageType.SESSIONINVITE: "SessionInvite",
    NeosMessageType.CREDITTRANSFER: "CreditTransfer",
    NeosMessageType.SUGARCUBES: "SugarCubes",
}

@dataclass
class NeosMessage:
    """Representation of a NeosVR message."""
    id: str
    senderId: str
    ownerId: str
    """The ownerId of a NeosMessage should start with `U-`"""
    sendTime: str
    recipientId: str
    messageType: NeosMessageType
    content: str

@dataclass
class NeosCloudVar:
    """Representation of NeosVR clound variable."""
    ownerId: str
    """The ownerId of a NeosCloudVar should start with `U-`"""
    path: str
    """The path of a NeosCloudVar should start with a `U-` for a user owned path and a `G-` for a group owned path."""
    value: str
    partitionKey: str
    rowKey: str
    timestamp: str
    eTag: str


class OwnerType(Enum):
    MACHING = "Machine"
    USER = "User"
    GROUP = "Group"
    INVALID = "Invalid"


@dataclass
class NeosCloudVarDefs:
    definitionOwnerId: str
    subpath: str
    variableType: str
    defaultValue: Optional[str]
    deleteScheduled: bool
    readPermissions: List[str]
    writePermissions: List[str]
    listPermissions: List[str]
    partitionKey: str
    rowKey: str
    timestamp: str
    eTag: str
