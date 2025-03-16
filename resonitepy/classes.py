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
    """ Enum representing the type of a Resonite record.
    """

    OBJECT = "object"
    """Represents an object record."""
    LINK = "link"
    """Represents a link record."""
    DIRECTORY = "directory"
    """Represents a directory record."""
    WORLD = "world"
    """Represents a world record."""
    TEXTURE = "texture"
    """Represents a texture record."""
    AUDIO = "audio"
    """Represents an audio record."""


@dataclass
class ResoniteRecordVersion:
    """ Data class representing the version of a Resonite record.
    """

    globalVersion: int
    """The global version of the record."""
    localVersion: int
    """The local version of the record."""
    lastModifyingUserId: Optional[str]
    """The ID of the user who last modified the record. (optional)"""
    lastModifyingMachineId: Optional[str]
    """The ID of the machine that last modified the record. (optional"""

@dataclass
class ResoniteRecord:
    """ Data class representing a Resonite record.
    """

    id: str
    """The ID of the record."""
    assetUri: Optional[str]
    """The URI of the asset associated with the record."""
    version: ResoniteRecordVersion
    """The version of the record."""
    name: str
    """The name of the record."""
    recordType: RecordType
    """The type of the record."""
    ownerName: str
    """The name of the owner of the record."""
    path: Optional[str]
    """The path of the record."""
    thumbnailUri: Optional[str]
    """The URI of the thumbnail associated with the record."""
    isPublic: bool
    """Whether the record is public."""
    isForPatrons: bool
    """Whether the record is for patrons."""
    isListed: bool
    """Whether the record is listed."""
    isDeleted: bool
    """Whether the record is deleted."""
    tags: Optional[list]
    """The tags associated with the record."""
    creationTime: Optional[datetime]
    """The creation time of the record."""
    lastModificationTime: datetime
    """The last modification time of the record."""
    randomOrder: int
    """The random order of the record."""
    visits: int
    """The number of visits to the record."""
    rating: int
    """The rating of the record."""
    ownerId: str
    """The ID of the owner of the record."""
    isReadOnly: bool
    """Whether the record is read only."""


@dataclass
class ResoniteLink(ResoniteRecord):
    """ Data class representing a Resonite link.
    """

    assetUri: ParseResult
    """The parsed URI of the asset associated with the link."""


@dataclass
class ResoniteDirectory(ResoniteRecord):
    """ Data class representing a Resonite directory.
    """

    lastModifyingMachineId: Optional[str]
    """The ID of the machine that last modified the directory."""
    ownerName: str
    """The name of the owner of the directory."""
    tags: List[str]
    """The tags associated with the directory."""
    creationTime: Optional[datetime]
    """The creation time of the directory."""

    @property
    def content_path(self) -> str:
        """The path of the content within the directory."""
        return str(PureWindowsPath(self.path, self.name))


@dataclass
class ResoniteObject(ResoniteRecord):
    """ Data class representing a Resonite object.
    """

    assetUri: str
    """The URI of the asset associated with the object."""
    lastModifyingMachineId: Optional[str]
    """ The ID of the machine that last modified the object."""
    ownerName: str
    """The name of the owner of the object."""
    tags: List[str]
    """The tags associated with the object."""
    creationTime: datetime
    """The creation time of the object."""

@dataclass
class ResoniteWorld(ResoniteRecord):
    """ Data class representing a Resonite world.
    """
    pass

@dataclass
class ResoniteTexture(ResoniteRecord):
    """ Data class representing a Resonite texture.
    """
    pass

@dataclass
class ResoniteAudio(ResoniteRecord):
    """ Data class representing a Resonite audio.
    """
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
    """ Data class representing a login details for authentication.
    """

    password: str
    """The password for authentication."""

    def build_dict(self):
        """ Returns a dictionary representation of the login details.

        Returns:
            dict: A dictionary containing the login details.

        Example:
            >>> LoginDetailsAuth("my_password").build_dict()
            {'$type': 'password', 'password': 'my_password', 'recoveryCode': None}
        """
        return {
            "$type": "password",
            "password": self.password,
            "recoveryCode": None
        }


@dataclass
class LoginDetails:
    """ Data class representing a login details.

    Raises:
        ResoniteException: If neither ownerId, username, nor email is provided during post-initialization.
        ResoniteException: If authentication details are not provided during post-initialization.
    """

    authentication: LoginDetailsAuth
    """The authentication details for the login."""
    ownerId: Optional[str] = None
    """The ownerId of the login which should start with an `U-`."""
    username: Optional[str] = None
    """The username of the login."""
    email: Optional[str] = None
    """The email of the login."""
    secretMachineId: str = field(default_factory=generate)
    """The secret machine ID for the login. See the generate class in the resonite.secrets module."""
    rememberMe: Optional[str] = False
    """The remember me option for the login."""

    def __post_init__(self):
        """ Performs post-initialization checks for a class instance."""
        if not self.ownerId and not self.username and not self.email:
            raise ResoniteException(
                'Either an ownerId, an username or an email is needed')
        if not self.authentication:
            raise ResoniteException('A password is needed')


@dataclass
class ProfileData:
    """ Data class representing a profile data.
    """

    iconUrl: Optional[str]
    """The URL of the profile icon."""
    tokenOutOut: Optional[List[str]]
    """The list of token outputs."""
    displayBadges: Optional[list]
    """The list of display badges."""
    tagline: Optional[str]
    """The tagline of the profile."""
    description: Optional[str]
    """The description of the profile."""


@dataclass
class Snapshot:
    """ Data class representing a snapshot of data.
    """

    totalCents: int
    """The total cents."""
    patreonRawCents: int
    """The raw cents from Patreon."""
    deltaCents: int
    """The delta cents."""
    pledgeCents: int
    """The pledge cents."""
    email: str
    """The email associated with the snapshot."""
    timestamp: str
    """The timestamp of the snapshot."""

@dataclass
class PatreonData:
    """ Data class representing a Patreon data.
    """

    isPatreonSupporter: bool
    """Whether the user is a Patreon supporter."""
    patreonId: Optional[str]
    """The Patreon ID of the user."""
    lastPatreonEmail: str
    """The last Patreon email associated with the user."""
    snapshots: List[Snapshot]
    """A list of snapshots associated with the user."""
    lastPatreonPledgeCents: int
    """The last Patreon pledge amount in cents."""
    lastTotalCents: int
    """The last total amount in cents."""
    minimumTotalUnits: int
    """The minimum total units."""
    externalCents: int
    """The external amount in cents."""
    lastExternalCents: int
    """The last external amount in cents."""
    hasSupported: bool
    """Whether the user has supported."""
    lastIsAnorak: Optional[bool] # Deprecated
    """Deprecated"""
    priorityIssue: int
    """The priority issue."""
    lastPlusActivationTime: Optional[datetime] # Depreacted
    """Deprecated"""
    lastActivationTime: Optional[datetime] # Deprecated
    """Deprecated"""
    lastPlusPledgeAmount: Optional[int] # Deprecated
    """Deprecated"""
    lastPaidPledgeAmount: int
    """The last paid pledge amount."""
    accountName: Optional[str] # Deprecated
    """Deprecated"""
    currentAccountType: Optional[int] # Deprecated
    """Deprecated"""
    currentAccountCents: Optional[int] # Deprecated
    """Deprecated"""
    pledgedAccountType: Optional[int] # Deprecated
    """Deprecated"""


@dataclass
class QuotaBytesSources:
    """ Data class representing the quota bytes sources.
    """

    base: int
    """The base quota bytes."""
    patreon: int
    """The Patreon quota bytes."""
    paid: int
    """The paid quota bytes."""
    mmc21_honorary: int
    """The MMC21 honorary quota bytes."""


@dataclass
class ResoniteUserQuotaBytesSources:
    """ Data class representing the quota bytes sources for a Resonite user.
    """

    base: int
    """The base quota bytes."""
    patreon: Optional[int]
    """The Patreon quota bytes."""


@dataclass
class ResoniteUserMigrationData:
    """ Data class representing the migration data for a Resonite user.
    """

    username: str
    """The username of the user."""
    email: Optional[str]
    """The email of the user."""
    userId: str
    """The ID of the user."""
    quotaBytes: int
    """The quota bytes of the user."""
    usedBytes: int
    """The used bytes of the user."""
    patreonData: Optional[PatreonData]
    """ The Patreon data of the user."""
    quotaBytesSources: Optional[ResoniteUserQuotaBytesSources]
    """The quota bytes sources of the user."""
    registrationDate: datetime
    """The registration date of the user."""


@dataclass
class ResoniteUserEntitlementShoutOut:
    """ Data class representing an entitlement shout-out for a Resonite user.
    """

    shoutoutType: str
    """The type of the shout-out."""
    friendlyDescription: str
    """The friendly description of the shout-out."""


@dataclass
class ResoniteUserEntitlementCredits:
    """ Data class representingan entitlement credit for a Resonite user.
    """

    creditType: str
    """The type of the credit."""
    friendlyDescription: str
    """The friendly description of the credit."""
    entitlementOrigins: list[str]
    """The entitlement origins."""


@dataclass
class ResoniteUserEntitlementGroupCreation:
    """ Data class representing the entitlement for the group creation for a Resonite user.
    """

    groupCount: int
    """The number of groups the user is entitled to create."""
    entitlementOrigins: list[str]
    """The entitlement origins."""


@dataclass
class ResoniteEntitlementDeleteRecovery:
    """ Data class representing the entitlement for deleting recovery data in Resonite.
    """

    entitlementOrigins: list[str]
    """The entitlement origins."""


@dataclass
class ResoniteUserEntitlementBadge:
    """ Data class representing an entitlement badge for a Resonite user.
    """

    badgeType: str
    """The type of the badge."""
    badgeCount: int
    """The count of the badge."""
    entitlementOrigins: list[str]
    """The entitlement origins."""


@dataclass
class ResoniteUserEntitlementHeadless:
    """ Data class representing a headless entitlement for a Resonite user.
    """

    friendlyDescription: str
    """The friendly description of the headless entitlement."""
    entitlementOrigins: list[str]
    """The entitlement origins."""


@dataclass
class ResoniteUserEntitlementExitMessage:
    """ Data class representing an exit message entitlement for a Resonite user.
    """

    isLifetime: bool
    """Indicates whether the entitlement is lifetime."""
    messageCount: int
    """The count of exit messages."""
    friendlyDescription: str
    """The friendly description of the exit message entitlement."""
    entitlementOrigins: list[str]
    """The entitlement origins."""


@dataclass
class ResoniteUserEntitlementStorageSpace:
    """ Data class representing a storage space entitlement for a Resonite user.
    """

    bytes: int
    """The amount of storage space in bytes."""
    maximumShareLevel: str
    """The maximum share level."""
    storageId: str
    """The ID of the storage space."""
    group: str
    """The group associated with the storage space."""
    startsOn: datetime
    """The start date of the entitlement."""
    expiresOn: datetime
    """The expiration date of the entitlement."""
    name: str
    """The name of the storage space."""
    description: str
    """The description of the storage space."""
    entitlementOrigins: list[str]
    """The entitlement origins."""

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
    """ Data class representing the Patreon supporter metadata.
    """

    isActiveSupporter: bool
    """Whether the user is an active supporter."""
    isActive: bool
    """Whether the user is an active."""
    totalSupportMonths: int
    """The total number of months of support."""
    totalSupportCents: int
    """The total amount of support in cents."""
    lastTierCents: int
    """The amount of the last tier in cents."""
    highestTierCents: int
    """The amount of the highest tier in cents."""
    lowestTierCents: int
    """The amount of the lowest tier in cents."""
    firstSupportTimestamp: datetime
    """The timestamp of the first support."""
    lastSupportTimestamp: datetime
    """The timestamp of the last support."""

@dataclass
class supporterMetadataStripe:
    pass

supporterMetadataTypeMapping = {
    'patreon': supporterMetadataPatreon,
    'stripe': supporterMetadataStripe,
}


@dataclass
class ResoniteUser:
    """ Data class representing a Resonite user.
    """

    id: str
    """The ID of the user."""
    username: str
    """The username of the user."""
    normalizedUsername: str
    """The normalized username of the user."""
    email: Optional[str]
    """The email of the user."""
    registrationDate: datetime
    """The registration date of the user."""
    isVerified: bool
    """Indicates whether the user is verified."""
    isLocked: bool
    """Whether the user is locked."""
    supressBanEvasion: bool
    """Whether ban evasion is suppressed for the user."""
    two_fa_login: bool
    """Whether two-factor authentication is enabled for login."""
    profile: Optional[ProfileData]
    """The profile data of the user."""
    supporterMetadata: Optional[List[
        supporterMetadataPatreon |
        supporterMetadataStripe
    ]]
    """The Patreon supporter metadata of the user."""
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
    """The entitlements of the user."""
    migratedData: Optional[ResoniteUserMigrationData]
    """The migrated data of the user."""
    tags: Optional[List[str]] = field(default_factory=list)
    """The tags associated with the user."""

@dataclass
class ResoniteUserMembership:
    id: str
    groupName: str
    isMigrated: bool
    ownerId: str

@dataclass
class WorldId:
    """ Data class representing a World ID.
    """

    ownerId: str
    """The owner ID of the world. Start with `U-`"""
    recordId: str
    """The record ID of the world."""

@dataclass
class ResoniteGroup:
    id: str
    adminUserId: str
    name: str
    isMigrated: bool

@dataclass
class ResoniteGroupMember:
    id: str
    isMigrated: bool
    ownerId: str

@dataclass
class ResoniteSessionUser:
    """ Data class representing a Resonite session user.
    """

    isPresent: bool
    """Whether the user is present."""
    userID: Optional[str]
    """The ID of the user."""
    username: str
    """The username of the user."""
    userSessionId: Optional[str]
    """The session ID of the user."""
    outputDevice: Optional[int]
    """The output device of the user."""

@dataclass
class ResoniteSession:
    """ Data class representing a Resonite session.
    """

    activeSessions: Optional[str]
    """The active sessions."""
    activeUsers: int
    """ The number of active users."""
    compatibilityHash: Optional[str]
    """The compatibility hash."""
    systemCompatibilityHash: Optional[str]
    """The system compatibility hash."""
    correspondingWorldId: Optional[WorldId]
    """The corresponding world ID."""
    description: Optional[str]
    """The description of the session."""
    accessLevel: str  # TODO: This should be an Enum instead
    """The access level of the session."""
    hasEnded: bool
    """Whether the session has ended."""
    headlessHost: bool
    """Whether the host is headless."""
    hostMachineId: str
    """The machine ID of the host."""
    hostUserSessionId: Optional[str]
    """The user session ID of the host."""
    hostUserId: Optional[str]
    """The user ID of the host."""
    hostUsername: str
    """The username of the host."""
    isValid: bool
    """Whether the session is valid."""
    joinedUsers: int
    """The number of joined users."""
    lastUpdate: datetime
    """The timestamp of the last update."""
    maxUsers: int
    """The maximum number of users."""
    mobileFriendly: bool
    """Whether the session is mobile-friendly."""
    name: str
    """The name of the session."""
    appVersion: str
    """The version of the app."""
    normalizedSessionId: str
    """The normalized session ID."""
    sessionBeginTime: datetime
    """The timestamp of the session begin time."""
    sessionId: str
    """The session ID."""
    nestedSessionIds: list  # TODO: This should be a list of objects
    """The nested session IDs."""
    parentSessionIds: list  # TODO: This should be a list of objects
    """The parent session IDs."""
    sessionURLs: List[str]
    """The URLs of the session."""
    sessionUsers: List[ResoniteSessionUser]
    """The users in the session."""
    tags: List[str]
    """The tags associated with the session."""
    thumbnailUrl: Optional[str]
    """The URL of the thumbnail."""
    totalActiveUsers: int
    """The total number of active users."""
    totalJoinedUsers: int
    """The total number of joined users."""
    hideFromListing: bool
    """Whether the session is hidden from listing."""
    dataModelAssemblies: list  # TODO: make it an object
    """Data model assemblies."""
    universeId: Optional[str]
    """The universe id of the session."""


@dataclass
class PublicRSAKey:
    """ Data class representing a public RSA key.
    """

    Exponent: str
    """The exponent of the RSA key."""
    Modulus: str
    """The modulus of the RSA key."""


class OnlineStatus(Enum):
    """ Enum representing the online status of a Resonite user.
    """

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
    """ Enum representing the access level of a Resonite session.
    """
    PRIVATE = 0
    """Private access level."""
    LAN = 1
    """LAN access level."""
    FRIENDS = 2
    """Contacts access level."""
    FRIENDSOFFRIENDS = 3
    """Contacts+ access level."""
    REGISTEREDUSERS = 4
    """Registered Users access level."""
    ANYONE = 5
    """Anyone access level."""

    def __str__(self):
        """Returns the string representation of the access level."""
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
    """ Data class representing an user status data.
    """

    activeSessions: Optional[List[ResoniteSession]]
    """The list of active sessions."""
    currentSession: Optional[ResoniteSession]
    """The current session."""
    compatibilityHash: Optional[str]
    """The compatibility hash."""
    currentHosting: bool
    """Whether the user is currently hosting a session."""
    currentSessionAccessLevel: CurrentResoniteSessionAccessLevel
    """The access level of the current session."""
    currentSessionHidden: bool
    """Whether the current session is hidden."""
    currentSessionId: Optional[str]
    """The ID of the current session."""
    isMobile: bool
    """Whether the user is on a mobile device."""
    lastStatusChange: datetime
    """The timestamp of the last status change."""
    neosVersion: Optional[str]
    """The version of Neos."""
    onlineStatus: OnlineStatus
    """The online status of the user."""
    OutputDevice: Optional[str]
    """The output device of the user."""
    publicRSAKey: Optional[PublicRSAKey]
    """The public RSA key of the user."""

@dataclass
class ResoniteUserStatus:
    """ Data class representing the status of a Resonite user.
    """

    onlineStatus: OnlineStatus
    """The online status of the user."""
    lastStatusChange: datetime
    """The timestamp of the last status change."""
    currentSessionAccessLevel: int
    """The access level of the current session."""
    currentSessionHidden: bool
    """Whether the current session is hidden."""
    currentHosting: bool
    """Whether the user is currently hosting a session."""
    compatibilityHash: Optional[str]
    """The compatibility hash."""
    neosVersion: Optional[str]
    """The version of Neos. """
    publicRSAKey: Optional[PublicRSAKey]
    """The public RSA key."""
    OutputDevice: Optional[str]
    """The output device."""
    isMobile: bool
    """Whether the user is on a mobile device."""

class ContactStatus(Enum):
    """ Enum representing the status of a contact.
    """

    ACCEPTED = "Accepted"
    """The contact request has been accepted."""
    IGNORED = "Ignored"
    """The contact request has been ignored."""
    REQUESTED = "Requested"
    """ The contact request has been sent but not yet accepted."""
    NONE = "None"
    """No contact status."""


contactStatusMapping = {
    ContactStatus.ACCEPTED: "Accepted",
    ContactStatus.IGNORED: "Ignored",
    ContactStatus.REQUESTED: "Requested",
    ContactStatus.NONE: "None",
}


@dataclass
class ResoniteContact:
    id: str
    contactUsername: str
    contactStatus: ContactStatus
    isAccepted: bool
    profile: Optional[ProfileData]
    latestMessageTime: datetime
    isMigrated: bool
    isCounterpartMigrated: bool
    ownerId: str
    universeId: Optional[str]

class ResoniteMessageType(Enum):
    """ Enum representing a Resonite message type.
    """

    TEXT = "Text"
    """Text type message."""
    OBJECT = "Object"
    """Object type message."""
    SOUND = "Sound"
    """Audio type message."""
    SESSIONINVITE = "SessionInvite"
    """Session invite type message."""
    INVITEREQUEST = "InviteRequest"
    """Invite request type message."""
    CREDITTRANSFER = "CreditTransfer"
    """Credit transfert type message."""
    SUGARCUBES = "SugarCubes"
    """Sugar cubes type message."""

ResoniteMessageTypeMapping = {
    ResoniteMessageType.TEXT: "Text",
    ResoniteMessageType.OBJECT: "Object",
    ResoniteMessageType.SOUND: "Sound",
    ResoniteMessageType.SESSIONINVITE: "SessionInvite",
    ResoniteMessageType.INVITEREQUEST: "InviteRequest",
    ResoniteMessageType.CREDITTRANSFER: "CreditTransfer",
    ResoniteMessageType.SUGARCUBES: "SugarCubes",
}


@dataclass
class ResoniteMessageContentText:
    content: str

    def __str__(self) -> str:
        return self.content

@dataclass
class ResoniteMessageContentObject:
    """ Data class representing the content of a Resonite object message.
    """

    id: str
    """The ID of the object."""
    ownerId: str
    """The ID of the object owner."""
    assetUri: str
    """The URI of the object asset."""
    version: Optional[ResoniteRecordVersion]
    """The version of the object record."""
    name: str
    """The name of the object."""
    recordType: RecordType
    """The type of the object record."""
    ownerName: Optional[str]
    """The name of the object owner."""
    tags: List[str]
    """The tags associated with the object."""
    path: Optional[str]
    """The path of the object."""
    thumbnailUri: str
    """The URI of the object thumbnail."""
    isPublic: bool
    """Whether the object is public."""
    isForPatrons: bool
    """Whether the object is for patrons."""
    isListed: bool
    """Whether the object is listed."""
    isReadOnly: bool
    """Whether the object is read-only."""
    lastModificationTime: datetime
    """The timestamp of the last modification."""
    creationTime: datetime
    """The timestamp of the creation."""
    firstPublishTime: Optional[datetime]
    """The timestamp of the first publish."""
    isDeleted: Optional[bool]
    """Whether the object is deleted."""
    visits: int
    """The number of visits."""
    rating: float
    """The rating of the object."""
    randomOrder: int
    """The random order of the object."""
    submissions: Optional[str]
    """The submissions of the object."""

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
    hostUserId: str
    hostUserSessionId: str
    compatibilityHash: Optional[str]
    universeId: Optional[str]
    appVersion: Optional[str]
    headlessHost: Optional[bool]
    sessionURLs: List[str]
    thumbnailUrl: Optional[str]
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
    dataModelAssemblies: list  # TODO: make it an object
    hideFromListing: bool
    systemCompatibilityHash: str

@dataclass
class ResoniteMessageContentRequestInvite:
    inviteRequestId: str
    userIdToInvite: str
    usernameToInvite: str
    requestingFromUserId: str
    requestingFromUsername: str
    forSessionId: Optional[str]
    forSessionName: Optional[str]
    isContactOfHost: Optional[str]
    response: Optional[str]
    invite: Optional[str]

@dataclass
class ResoniteMessageContentSound:
    id: str
    ownerId: Optional[str]
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
    assetManifest: list  # TODO: make it an object
    isForPatrons: bool
    version: dict  # TODO: make it an object
    isDeleted: bool
    isReadOnly: Optional[bool]



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
    readTime: Optional[datetime]
    otherId: str
    lastUpdateTime: datetime
    content: Optional[
        ResoniteMessageContentText
        | ResoniteMessageContentSessionInvite
        | ResoniteMessageContentRequestInvite
        | ResoniteMessageContentObject
        | ResoniteMessageContentSound
    ]

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


@dataclass
class Platform:
    name: str
    shortNamePrefix: str
    abbreviation: str
    domain: str
    moderationURL: str
    supportURL: str
    policiesPage: str
    email: str
    discordInviteURL: str
    patreonURL: str
    webRecordEndpoint: str
    webSessionEndpoint: str
    groupId: str
    teamGroupId: str
    computeGroupId: str
    networkGroupId: str
    appUsername: str
    devBotUsername: str
    computeUsername: str
    networkUsername: str
    appUserId: str
    devBotUserId: str
    computeUserId: str
    networkUserId: str
    authScheme: str
    appScheme: str
    dbScheme: str
    sessionScheme: str
    recordScheme: str
    userSessionScheme: str
    steamAppId: str
    discordAppId: int
