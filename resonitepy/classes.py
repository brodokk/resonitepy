"""
This module define some of the Resonite API json
responce under usable python classes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import PureWindowsPath
from typing import List, Optional

from resonitepy.secrets import generate
from resonitepy.exceptions import ResoniteException

from urllib.parse import ParseResult


class RecordType(Enum):
    """Representation of the type of a Resonite record."""
    OBJECT = "object"
    LINK = "link"
    DIRECTORY = "directory"
    WORLD = "world"
    TEXTURE = "texture"
    AUDIO = "audio"


@dataclass
class ResoniteRecordVersion:
    globalVersion: int
    localVersion: int
    lastModifyingUserId: Optional[str]
    lastModifyingMachineId: Optional[str]

@dataclass
class ResoniteRecord:
    """Representation of a Resonite record."""
    id: str
    assetUri: Optional[str]
    version: ResoniteRecordVersion
    name: str
    recordType: RecordType
    ownerName: str
    path: Optional[str]
    thumbnailUri: Optional[str]
    isPublic: bool
    isForPatrons: bool
    isListed: bool
    isDeleted: bool
    tags: Optional[list]
    creationTime: Optional[datetime]
    lastModificationTime: datetime
    randomOrder: int
    visits: int
    rating: int
    ownerId: str


@dataclass
class ResoniteLink(ResoniteRecord):
    """Representation of a Resonite link."""
    assetUri: ParseResult


@dataclass
class ResoniteDirectory(ResoniteRecord):
    """Representation of a Resonite directory."""
    lastModifyingMachineId: Optional[str]
    ownerName: str
    tags: List[str]
    creationTime: Optional[datetime]

    @property
    def content_path(self) -> str:
        return str(PureWindowsPath(self.path, self.name))


@dataclass
class ResoniteObject(ResoniteRecord):
    """Represenation of a Resonite object."""
    assetUri: str
    lastModifyingMachineId: Optional[str]
    ownerName: str
    tags: List[str]
    creationTime: datetime

@dataclass
class ResoniteWorld(ResoniteRecord):
    """Representation of a Resonite world."""
    pass

@dataclass
class ResoniteTexture(ResoniteRecord):
    """Representation of a Resonite texture."""
    pass

@dataclass
class ResoniteAudio(ResoniteRecord):
    """Representation of a Resonite audio."""
    pass


recordTypeMapping = {
    RecordType.DIRECTORY: ResoniteDirectory,
    RecordType.LINK: ResoniteLink,
    RecordType.OBJECT: ResoniteObject,
    RecordType.WORLD: ResoniteWorld,
    RecordType.TEXTURE: ResoniteTexture,
    RecordType.AUDIO: ResoniteAudio,
}


@dataclass
class LoginDetailsAuth:
    password: str

    def build_dict(self):
        return {
            "$type": "password",
            "password": self.password,
            "recoveryCode": None
        }


@dataclass
class LoginDetails:
    authentication: LoginDetailsAuth
    """Representation of a Resonite login detail."""
    ownerId: Optional[str] = None
    """The ownerId of a LoginDetails should start with `U-`"""
    username: Optional[str] = None
    email: Optional[str] = None
    secretMachineId: str = field(default_factory=generate)
    """See the generate class in the resonite.secrets module."""
    rememberMe: Optional[str] = False

    def __post_init__(self):
        if not self.ownerId and not self.username and not self.email:
            raise ResoniteException(
                'Either an ownerId, an username or an email is needed')
        if not self.authentication:
            raise ResoniteException('A password is needed')


@dataclass
class ProfileData:
    """Representation of a Resonite profile data."""
    iconUrl: Optional[str]
    tokenOutOut: Optional[List[str]]
    displayBadges: Optional[list]
    tagline: Optional[str]
    description: Optional[str]


@dataclass
class Snapshot:
    totalCents: int
    patreonRawCents: int
    deltaCents: int
    pledgeCents: int
    email: str
    timestamp: str

@dataclass
class PatreonData:
    """Representation of a Resonite Patreon data."""
    isPatreonSupporter: bool
    patreonId: Optional[str]
    lastPatreonEmail: str
    snapshots: List[Snapshot]
    lastPatreonPledgeCents: int
    lastTotalCents: int
    minimumTotalUnits: int
    externalCents: int
    lastExternalCents: int
    hasSupported: bool
    lastIsAnorak: Optional[bool] # Deprecated
    priorityIssue: int
    lastPlusActivationTime: Optional[datetime] # Depreacted
    lastActivationTime: Optional[datetime] # Deprecated
    lastPlusPledgeAmount: Optional[int] # Deprecated
    lastPaidPledgeAmount: int
    accountName: Optional[str] # Deprecated
    currentAccountType: Optional[int] # Deprecated
    currentAccountCents: Optional[int] # Deprecated
    pledgedAccountType: Optional[int] # Deprecated


@dataclass
class QuotaBytesSources:
    base: int
    patreon: int
    paid: int
    mmc21_honorary: int


@dataclass
class ResoniteUserQuotaBytesSources:
    base: int
    patreon: Optional[int]


@dataclass
class ResoniteUserMigrationData:
    username: str
    email: str
    userId: str
    quotaBytes: int
    usedBytes: int
    patreonData: PatreonData
    quotaBytesSources: Optional[ResoniteUserQuotaBytesSources]
    registrationDate: datetime


@dataclass
class ResoniteUserEntitlementShoutOut:
    shoutoutType: str
    friendlyDescription: str


@dataclass
class ResoniteUserEntitlementCredits:
    creditType: str
    friendlyDescription: str


@dataclass
class ResoniteUserEntitlementGroupCreation:
    groupCount: int


@dataclass
class ResoniteEntitlementDeleteRecovery:
    pass


@dataclass
class ResoniteUserEntitlementBadge:
    badgeType: str
    badgeCount: int


@dataclass
class ResoniteUserEntitlementHeadless:
    friendlyDescription: str


@dataclass
class ResoniteUserEntitlementExitMessage:
    isLifetime: bool
    messageCount: int
    friendlyDescription: str


@dataclass
class ResoniteUserEntitlementStorageSpace:
    bytes: int
    maximumShareLevel: int
    storageId: str
    group: str
    startsOn: datetime
    expiresOn: datetime
    name: str
    description: str

resoniteUserEntitlementTypeMapping = {
    'shoutOut': ResoniteUserEntitlementShoutOut,
    'credits': ResoniteUserEntitlementCredits,
    'groupCreation': ResoniteUserEntitlementGroupCreation,
    'deleteRecovery': ResoniteEntitlementDeleteRecovery,
    'badge': ResoniteUserEntitlementBadge,
    'headless': ResoniteUserEntitlementHeadless,
    'exitMessage': ResoniteUserEntitlementExitMessage,
    'storageSpace': ResoniteUserEntitlementStorageSpace,
}


@dataclass
class supporterMetadataPatreon:
    isActiveSupporter: bool
    totalSupportMonths: int
    totalSupportCents: int
    lastTierCents: int
    highestTierCents: int
    lowestTierCents: int
    firstSupportTimestamp: datetime
    lastSupportTimestamp: datetime


supporterMetadataTypeMapping = {
    'patreon': supporterMetadataPatreon,
}


@dataclass
class ResoniteUser:
    """Representation of a Resonite user."""
    id: str
    username: str
    normalizedUsername: str
    email: str
    registrationDate: datetime
    isVerified: bool
    isLocked: bool
    supressBanEvasion: bool
    two_fa_login: bool
    profile: Optional[ProfileData]
    supporterMetadata: Optional[List[
        supporterMetadataPatreon
    ]]
    entitlements: Optional[List[
        ResoniteUserEntitlementShoutOut |
        ResoniteUserEntitlementCredits |
        ResoniteUserEntitlementGroupCreation |
        ResoniteEntitlementDeleteRecovery |
        ResoniteUserEntitlementBadge |
        ResoniteUserEntitlementHeadless |
        ResoniteUserEntitlementExitMessage |
        ResoniteUserEntitlementStorageSpace
    ]]
    migratedData: Optional[ResoniteUserMigrationData]
    tags: Optional[List[str]] = field(default_factory=list)

@dataclass
class WorldId:
    """Representation of a world id."""
    ownerId: str
    """The ownerId of a WorldId should start with `U-`"""
    recordId: str

@dataclass
class ResoniteSessionUser:
    """Representation of a session user."""
    isPresent: bool
    userID: Optional[str]
    username: str
    userSessionId: Optional[str]
    outputDevice: Optional[int]

@dataclass
class ResoniteSession:
    """Representation of a session."""
    activeSessions: Optional[str]
    activeUsers: int
    compatibilityHash: Optional[str]
    correspondingWorldId: Optional[WorldId]
    description: Optional[str]
    hasEnded: bool
    headlessHost: bool
    hostMachineId: str
    hostUserSessionId: str
    hostUserId: Optional[str]
    hostUsername: str
    isValid: bool
    joinedUsers: int
    lastUpdate: datetime
    maxUsers: int
    mobileFriendly: bool
    name: str
    appVersion: str
    normalizedSessionId: str
    sessionBeginTime: datetime
    sessionId: str
    sessionURLs: List[str]
    sessionUsers: List[ResoniteSessionUser]
    tags: List[str]
    thumbnailUrl: Optional[str]
    totalActiveUsers: int
    totalJoinedUsers: int
    hideFromListing: bool


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


class CurrentResoniteSessionAccessLevel(Enum):
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


currentResoniteSessionAccessLevelMapping = {
    CurrentResoniteSessionAccessLevel.PRIVATE: 0,
    CurrentResoniteSessionAccessLevel.LAN: 1,
    CurrentResoniteSessionAccessLevel.FRIENDS: 2,
    CurrentResoniteSessionAccessLevel.FRIENDSOFFRIENDS: 3,
    CurrentResoniteSessionAccessLevel.REGISTEREDUSERS: 4,
    CurrentResoniteSessionAccessLevel.ANYONE: 5,
}


@dataclass
class UserStatusData:
    """Representation of a Resonite user status data."""
    activeSessions: Optional[List[ResoniteSession]]
    currentSession: Optional[ResoniteSession]
    compatibilityHash: Optional[str]
    currentHosting: bool
    currentSessionAccessLevel: CurrentResoniteSessionAccessLevel
    currentSessionHidden: bool
    currentSessionId: Optional[str]
    isMobile: bool
    lastStatusChange: datetime
    neosVersion: Optional[str]
    onlineStatus: OnlineStatus
    OutputDevice: Optional[str]
    publicRSAKey: Optional[PublicRSAKey]

@dataclass
class ResoniteUserStatus:
    """Represenation of a Resonite user status."""
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

class ContactStatus(Enum):
    """Representation of a ContactStatus."""
    ACCEPTED = "Accepted"
    IGNORED = "Ignored"
    REQUESTED = "Requested"
    NONE = "None"


contactStatusMapping = {
    ContactStatus.ACCEPTED: "Accepted",
    ContactStatus.IGNORED: "Ignored",
    ContactStatus.REQUESTED: "Requested",
    ContactStatus.NONE: "None",
}


@dataclass
class ResoniteContact:
    """Representation of a Resonite contact."""
    id: str
    contactUsername: str
    contactStatus: ContactStatus
    isAccepted: bool
    profile: Optional[ProfileData]
    latestMessageTime: datetime
    isMigrated: bool
    isCounterpartMigrated: bool
    ownerId: str

class ResoniteMessageType(Enum):
    TEXT = "Text"
    OBJECT = "Object"
    SOUND = "Sound"
    SESSIONINVITE = "SessionInvite"
    CREDITTRANSFER = "CreditTransfer"
    SUGARCUBES = "SugarCubes"

ResoniteMessageTypeMapping = {
    ResoniteMessageType.TEXT: "Text",
    ResoniteMessageType.OBJECT: "Object",
    ResoniteMessageType.SOUND: "Sound",
    ResoniteMessageType.SESSIONINVITE: "SessionInvite",
    ResoniteMessageType.CREDITTRANSFER: "CreditTransfer",
    ResoniteMessageType.SUGARCUBES: "SugarCubes",
}


class ResoniteMessageContentText(str):
    def __new__(cls, *args, **kw):
        return str.__new__(cls, *args, **kw)


@dataclass
class ResoniteMessageContentObject:
    id: str
    ownerId: str
    assetUri: str
    version: Optional[ResoniteRecordVersion]
    name: str
    recordType: RecordType
    ownerName: Optional[str]
    tags: List[str]
    path: Optional[str]
    thumbnailUri: str
    isPublic: bool
    isForPatrons: bool
    isListed: bool
    lastModificationTime: datetime
    creationTime: datetime
    firstPublishTime: Optional[datetime]
    isDeleted: Optional[bool]
    visits: int
    rating: float
    randomOrder: int
    sumbissions: Optional[str]

@dataclass
class ResoniteMessageContentSessionInvite:
    name: str
    description: Optional[str]
    correspondingWorldId: Optional[WorldId]
    tags: List[str]
    sessionId: str
    normalizedSessionId: str
    hostMachineId: str
    hostUsername: str
    compatibilityHash: Optional[str]
    universeId: Optional[str]
    appVersion: Optional[str]
    headlessHost: Optional[bool]
    sessionURLs: List[str]
    parentSessionIds: Optional[List[str]]
    nestedSessionIds: Optional[List[str]]
    sessionUsers: List[ResoniteSessionUser]
    thumbnail: Optional[str]
    joinedUsers: int
    activeUsers: int
    totalActiveUsers: int
    totalJoinedUsers: int
    maxUsers: int
    mobileFriendly: bool
    sessionBeginTime: datetime
    lastUpdate: datetime
    accessLevel: str
    broadcastKey: Optional[str]


@dataclass
class ResoniteMessageContentSound:
    id: str
    OwnerId: Optional[str]
    assetUri: str
    globalVersion: Optional[int]
    localVersion: Optional[int]
    lastModifyingUserId: Optional[str]
    lastModifyingMachineId: Optional[str]
    name: str
    recordType: RecordType
    ownerName: Optional[str]
    tags: List[str]
    path: Optional[str]
    isPublic: bool
    isForPatron: Optional[bool]
    isListed: bool
    lastModificationTime: datetime
    creationTime: datetime
    firstPublishTime: Optional[datetime]
    visits: int
    rating: float
    randomOrder: int
    submissions: Optional[str]
    neosDBmanifest: Optional[list]



@dataclass
class ResoniteMessage:
    """Representation of a Resonite message."""
    id: str
    senderId: str
    ownerId: str
    """The ownerId of a ResoniteMessage should start with `U-`"""
    sendTime: str
    recipientId: str
    messageType: ResoniteMessageType
    senderUserSessionId: Optional[str]
    isMigrated: bool
    readTime: datetime
    otherId: str
    lastUpdateTime: datetime
    content: ResoniteMessageContentText | ResoniteMessageContentSessionInvite | ResoniteMessageContentObject | ResoniteMessageContentSound

@dataclass
class ResoniteCloudVar:
    """Representation of Resonite clound variable."""
    ownerId: str
    """The ownerId of a ResoniteCloudVar should start with `U-`"""
    path: str
    """The path of a ResoniteCloudVar should start with a `U-` for a user owned path and a `G-` for a group owned path."""
    value: Optional[str]
    partitionKey: str
    rowKey: str
    timestamp: Optional[str]
    eTag: Optional[str]


class OwnerType(Enum):
    MACHING = "Machine"
    USER = "User"
    GROUP = "Group"
    INVALID = "Invalid"


@dataclass
class ResoniteCloudVarDefs:
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