"""
This module define some of the Resonite API json
responce under usable python classes.
"""

import json
import logging
import os
from dataclasses import field
from datetime import datetime
from enum import Enum
from pathlib import PureWindowsPath

from typing import Annotated, List, Literal, Optional
from urllib.parse import ParseResult, urlparse
from pydantic import BeforeValidator, ConfigDict, model_validator, Field
from pydantic.dataclasses import dataclass as pydantic_dataclass

from resonitepy.secrets import generate
from resonitepy.exceptions import ResoniteException

_RESONITE_CLASS_CONFIG = ConfigDict(
    extra='allow',
    arbitrary_types_allowed=True,
    validate_by_name=True,
    validate_by_alias=True,
)

_TRACK_API_FIELDS = os.environ.get("RESONITEPY_DRIFT") == "1"


def _record_api_fields(cls, data, handler):
    """ Records which fields the API actually sent, for drift detection in test.py
    """
    keys = set(data.keys()) if isinstance(data, dict) else None
    obj = handler(data)
    if keys is not None:
        object.__setattr__(obj, "__api_fields__", keys)
    return obj


def resonite_class(cls):
    if _TRACK_API_FIELDS:
        cls.__record_api_fields__ = model_validator(mode="wrap")(classmethod(_record_api_fields))
    return pydantic_dataclass(config=_RESONITE_CLASS_CONFIG, kw_only=True)(cls)

logger = logging.getLogger(__name__)

class UnknownEnumMixin:

    @classmethod
    def _missing_(cls, value):
        logger.warning(
            "Unknown %s value %r, falling back to %s.UNKNOWN",
            cls.__name__, value, cls.__name__,
        )
        return cls.UNKNOWN

class RecordType(UnknownEnumMixin, Enum):
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
    UNKNOWN = "__unknown__"


@resonite_class
class ResoniteRecordVersion:
    """ Data class representing the version of a Resonite record.
    """

    globalVersion: int
    """The global version of the record."""
    localVersion: int
    """The local version of the record."""
    lastModifyingUserId: Optional[str] = None
    """The ID of the user who last modified the record. (optional)"""
    lastModifyingMachineId: Optional[str] = None
    """The ID of the machine that last modified the record. (optional"""

@resonite_class
class ResoniteRecord:
    """ Data class representing a Resonite record.
    """

    id: str
    """The ID of the record."""
    assetUri: Optional[str] = None
    """The URI of the asset associated with the record."""
    version: ResoniteRecordVersion
    """The version of the record."""
    name: str
    """The name of the record."""
    recordType: RecordType
    """The type of the record."""
    ownerName: str
    """The name of the owner of the record."""
    path: Optional[str] = None
    """The path of the record."""
    thumbnailUri: Optional[str] = None
    """The URI of the thumbnail associated with the record."""
    isPublic: bool
    """Whether the record is public."""
    isForPatrons: bool
    """Whether the record is for patrons."""
    isListed: bool
    """Whether the record is listed."""
    isDeleted: bool
    """Whether the record is deleted."""
    tags: Optional[list] = None
    """The tags associated with the record."""
    creationTime: Optional[datetime] = None
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


@resonite_class
class ResoniteLink(ResoniteRecord):
    """ Data class representing a Resonite link.
    """

    assetUri: Annotated[
        ParseResult,
        BeforeValidator(lambda v: urlparse(v) if isinstance(v, str) else v),
    ]
    """The parsed URI of the asset associated with the link."""


@resonite_class
class ResoniteAssetManifestEntry:
    """ Data class representing an asset referenced by a record.
    """

    hash: str
    """The hash of the asset in the Resonite asset database."""
    bytes: int
    """The size of the asset in bytes."""


@resonite_class
class ResoniteDirectory(ResoniteRecord):
    """ Data class representing a Resonite directory.
    """

    lastModifyingMachineId: Optional[str] = None
    """The ID of the machine that last modified the directory."""
    ownerName: str
    """The name of the owner of the directory."""
    tags: List[str]
    """The tags associated with the directory."""
    creationTime: Optional[datetime] = None
    """The creation time of the directory."""
    migrationMetadata: Optional[dict] = None
    assetManifest: Optional[List[ResoniteAssetManifestEntry]] = None

    @property
    def content_path(self) -> str:
        """The path of the content within the directory."""
        return str(PureWindowsPath(self.path, self.name))


@resonite_class
class ResoniteObject(ResoniteRecord):
    """ Data class representing a Resonite object.
    """

    assetUri: str
    """The URI of the asset associated with the object."""
    lastModifyingMachineId: Optional[str] = None
    """ The ID of the machine that last modified the object."""
    ownerName: str
    """The name of the owner of the object."""
    tags: List[str]
    """The tags associated with the object."""
    creationTime: datetime
    """The creation time of the object."""

@resonite_class
class ResoniteWorld(ResoniteRecord):
    """ Data class representing a Resonite world.
    """
    pass

@resonite_class
class ResoniteTexture(ResoniteRecord):
    """ Data class representing a Resonite texture.
    """
    pass

@resonite_class
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


@resonite_class
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


@resonite_class
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


@resonite_class
class ProfileData:
    """ Data class representing a profile data.
    """

    iconUrl: Optional[str] = None
    """The URL of the profile icon."""
    tokenOutOut: Optional[List[str]] = None
    """The list of token outputs."""
    displayBadges: Optional[list] = None
    """The list of display badges."""
    tagline: Optional[str] = None
    """The tagline of the profile."""
    description: Optional[str] = None
    """The description of the profile."""
    pronouns: Optional[str] = None
    """The pronouns of the profile."""


@resonite_class
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

@resonite_class
class PatreonData:
    """ Data class representing a Patreon data.
    """

    isPatreonSupporter: bool
    """Whether the user is a Patreon supporter."""
    patreonId: Optional[str] = None
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
    lastIsAnorak: Optional[bool] = None # Deprecated
    """Deprecated"""
    priorityIssue: int
    """The priority issue."""
    lastPlusActivationTime: Optional[datetime] = None # Depreacted
    """Deprecated"""
    lastActivationTime: Optional[datetime] = None # Deprecated
    """Deprecated"""
    lastPlusPledgeAmount: Optional[int] = None # Deprecated
    """Deprecated"""
    lastPaidPledgeAmount: int
    """The last paid pledge amount."""
    accountName: Optional[str] = None # Deprecated
    """Deprecated"""
    currentAccountType: Optional[int] = None # Deprecated
    """Deprecated"""
    currentAccountCents: Optional[int] = None # Deprecated
    """Deprecated"""
    pledgedAccountType: Optional[int] = None # Deprecated
    """Deprecated"""


@resonite_class
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


@resonite_class
class ResoniteUserQuotaBytesSources:
    """ Data class representing the quota bytes sources for a Resonite user.
    """

    base: int
    """The base quota bytes."""
    patreon: Optional[int] = None
    """The Patreon quota bytes."""
    paid: Optional[int] = None
    """The paid quota bytes."""


@resonite_class
class ResoniteUserMigrationData:
    """ Data class representing the migration data for a Resonite user.
    """

    username: str
    """The username of the user."""
    email: Optional[str] = None
    """The email of the user."""
    userId: str
    """The ID of the user."""
    quotaBytes: int
    """The quota bytes of the user."""
    usedBytes: int
    """The used bytes of the user."""
    patreonData: Optional[PatreonData] = None
    """ The Patreon data of the user."""
    quotaBytesSources: Optional[ResoniteUserQuotaBytesSources] = None
    """The quota bytes sources of the user."""
    registrationDate: datetime
    """The registration date of the user."""

@resonite_class
class ResoniteUserEntitlementUnknown:
    """ Fallback for entitlement types this module doesn't know yet.
    """
    type_: str = Field(alias='$type', default='__unknown__')

@resonite_class
class ResoniteUserEntitlementShoutOut:
    """ Data class representing an entitlement shout-out for a Resonite user.
    """

    type_: Literal['shoutOut'] = Field(alias='$type', default='shoutOut')
    """The $type tag sent by the API for this entitlement."""
    shoutoutType: str
    """The type of the shout-out."""
    friendlyDescription: str
    """The friendly description of the shout-out."""


@resonite_class
class ResoniteUserEntitlementCredits:
    """ Data class representingan entitlement credit for a Resonite user.
    """

    type_: Literal['credits'] = Field(alias='$type', default='credits')
    """The $type tag sent by the API for this entitlement."""
    creditType: str
    """The type of the credit."""
    friendlyDescription: str
    """The friendly description of the credit."""
    entitlementOrigins: list[str]
    """The entitlement origins."""


@resonite_class
class ResoniteUserEntitlementGroupCreation:
    """ Data class representing the entitlement for the group creation for a Resonite user.
    """

    type_: Literal['groupCreation'] = Field(alias='$type', default='groupCreation')
    """The $type tag sent by the API for this entitlement."""
    groupCount: int
    """The number of groups the user is entitled to create."""
    entitlementOrigins: list[str]
    """The entitlement origins."""


@resonite_class
class ResoniteEntitlementDeleteRecovery:
    """ Data class representing the entitlement for deleting recovery data in Resonite.
    """

    type_: Literal['deleteRecovery'] = Field(alias='$type', default='deleteRecovery')
    """The $type tag sent by the API for this entitlement."""
    entitlementOrigins: list[str]
    """The entitlement origins."""


@resonite_class
class ResoniteUserEntitlementBadge:
    """ Data class representing an entitlement badge for a Resonite user.
    """

    type_: Literal['badge'] = Field(alias='$type', default='badge')
    """The $type tag sent by the API for this entitlement."""
    badgeType: str
    """The type of the badge."""
    badgeCount: int
    """The count of the badge."""
    entitlementOrigins: list[str]
    """The entitlement origins."""


@resonite_class
class ResoniteUserEntitlementHeadless:
    """ Data class representing a headless entitlement for a Resonite user.
    """

    type_: Literal['headless'] = Field(alias='$type', default='headless')
    """The $type tag sent by the API for this entitlement."""
    friendlyDescription: str
    """The friendly description of the headless entitlement."""
    entitlementOrigins: list[str]
    """The entitlement origins."""


@resonite_class
class ResoniteUserEntitlementExitMessage:
    """ Data class representing an exit message entitlement for a Resonite user.
    """

    type_: Literal['exitMessage'] = Field(alias='$type', default='exitMessage')
    """The $type tag sent by the API for this entitlement."""
    isLifetime: bool
    """Indicates whether the entitlement is lifetime."""
    messageCount: int
    """The count of exit messages."""
    friendlyDescription: str
    """The friendly description of the exit message entitlement."""
    entitlementOrigins: list[str]
    """The entitlement origins."""


@resonite_class
class ResoniteUserEntitlementStorageSpace:
    """ Data class representing a storage space entitlement for a Resonite user.
    """

    type_: Literal['storageSpace'] = Field(alias='$type', default='storageSpace')
    """The $type tag sent by the API for this entitlement."""
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

@resonite_class
class supporterMetadataUnknown:
    """ Fallback for supporter metadata types this module doesn't know yet.
    """

@resonite_class
class supporterMetadataPatreon:
    """ Data class representing the Patreon supporter metadata.
    """

    type_: Literal['patreon'] = Field(alias='$type', default='patreon')
    """The $type tag sent by the API for this supporter metadata."""
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

@resonite_class
class supporterMetadataStripe:
    type_: Literal['stripe'] = Field(alias='$type', default='stripe')
    totalSupportCents: int
    firstSupportTimestamp: str
    lowestTierCents: int
    lastTierCents: int
    isActive: bool
    isActiveSupporter: bool
    highestTierCents: int
    lastSupportTimestamp: str
    totalSupportMonths: int


@resonite_class
class supporterMetadataPromo:
    type_: Literal['promo'] = Field(alias='$type', default='promo')
    isActiveSupporter: bool
    isActive: bool
    totalSupportMonths: int
    totalSupportCents: int
    lastTierCents: int
    highestTierCents: int
    lowestTierCents: int
    firstSupportTimestamp: datetime
    lastSupportTimestamp: datetime


@resonite_class
class ResoniteUser:
    """ Data class representing a Resonite user.
    """

    id: str
    """The ID of the user."""
    username: str
    """The username of the user."""
    normalizedUsername: str
    """The normalized username of the user."""
    alternateNormalizedNames: Optional[list[str]] = None
    """The alternate normalized username of the user."""
    email: Optional[str] = None
    """The email of the user."""
    registrationDate: datetime
    """The registration date of the user."""
    isVerified: bool
    """Indicates whether the user is verified."""
    isLocked: bool
    """Whether the user is locked."""
    supressBanEvasion: bool
    """Whether ban evasion is suppressed for the user."""
    two_fa_login: Optional[bool] = Field(alias='2fa_login', default=None)
    """Whether two-factor authentication is enabled for login."""
    profile: Optional[ProfileData] = None
    """The profile data of the user."""
    supporterMetadata: Optional[List[
        Annotated[
            supporterMetadataPatreon
            | supporterMetadataStripe
            | supporterMetadataPromo,
            Field(discriminator='type_'),
        ]
        | supporterMetadataUnknown
    ]] = None
    """The Patreon supporter metadata of the user."""
    entitlements: Optional[List[
        Annotated[
            ResoniteUserEntitlementShoutOut
            | ResoniteUserEntitlementCredits
            | ResoniteUserEntitlementGroupCreation
            | ResoniteEntitlementDeleteRecovery
            | ResoniteUserEntitlementBadge
            | ResoniteUserEntitlementHeadless
            | ResoniteUserEntitlementExitMessage
            | ResoniteUserEntitlementStorageSpace,
            Field(discriminator='type_'),
        ]
        | ResoniteUserEntitlementUnknown
    ]] = None
    """The entitlements of the user."""
    migratedData: Optional[ResoniteUserMigrationData] = None
    """The migrated data of the user."""
    """The tags associated with the user."""
    isActiveSupporter: bool
    promoCode: Optional[str] = None
    tags: Optional[List[str]] = field(default_factory=list)

@resonite_class
class ResoniteUserMembership:
    id: str
    groupName: str
    isMigrated: bool
    ownerId: str

@resonite_class
class WorldId:
    """ Data class representing a World ID.
    """

    ownerId: str
    """The owner ID of the world. Start with `U-`"""
    recordId: str
    """The record ID of the world."""

@resonite_class
class ResoniteGroup:
    id: str
    adminUserId: str
    name: str
    isMigrated: bool

@resonite_class
class ResoniteGroupMember:
    id: str
    isMigrated: bool
    ownerId: str

class CurrentResoniteSessionAccessLevel(UnknownEnumMixin, Enum):
    """ Enum representing the access level of a Resonite session.
    """
    PRIVATE = "Private"
    """Private access level."""
    LAN = "LAN"
    """LAN access level."""
    FRIENDS = "Contacts"
    """Contacts access level."""
    FRIENDSOFFRIENDS = "ContactsPlus"
    """Contacts+ access level."""
    REGISTEREDUSERS = "RegisteredUsers"
    """Registered Users access level."""
    ANYONE = "Anyone"
    """Anyone access level."""
    UNKNOWN = "__unknown__"

    def __str__(self):
        """Returns the string representation of the access level."""
        text = {
            'PRIVATE': 'Private',
            'LAN': 'LAN',
            'FRIENDS': 'Contacts',
            'FRIENDSOFFRIENDS': 'Contacts+',
            'REGISTEREDUSERS': 'Registered Users',
            'ANYONE': 'Anyone',
            'UNKNOWN': 'Unknown'
        }
        return text[self.name]


@resonite_class
class ResoniteSessionUser:
    """ Data class representing a Resonite session user.
    """

    isPresent: bool
    """Whether the user is present."""
    userID: Optional[str] = None
    """The ID of the user."""
    username: str
    """The username of the user."""
    userSessionId: Optional[str] = None
    """The session ID of the user."""
    outputDevice: Optional[int] = None
    """The output device of the user."""

@resonite_class
class DataModelAssemblies:
    name: str
    compatibilityHash: str

@resonite_class
class ResoniteSession:
    """ Data class representing a Resonite session.
    """

    activeSessions: Optional[str] = None
    """The active sessions."""
    activeUsers: int
    """ The number of active users."""
    compatibilityHash: Optional[str] = None
    """The compatibility hash."""
    systemCompatibilityHash: Optional[str] = None
    """The system compatibility hash."""
    correspondingWorldId: Optional[WorldId] = None
    """The corresponding world ID."""
    description: Optional[str] = None
    """The description of the session."""
    accessLevel: CurrentResoniteSessionAccessLevel
    """The access level of the session."""
    hasEnded: bool
    """Whether the session has ended."""
    headlessHost: bool
    """Whether the host is headless."""
    hostMachineId: str
    """The machine ID of the host."""
    hostUserSessionId: Optional[str] = None
    """The user session ID of the host."""
    hostUserId: Optional[str] = None
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
    nestedSessionIds: List[str]
    """The IDs of the sessions nested under this session."""
    parentSessionIds: List[str]
    """The IDs of the parent sessions of this session."""
    sessionURLs: List[str]
    """The URLs of the session."""
    sessionUsers: List[ResoniteSessionUser]
    """The users in the session."""
    tags: List[str]
    """The tags associated with the session."""
    thumbnailUrl: Optional[str] = None
    """The URL of the thumbnail."""
    totalActiveUsers: int
    """The total number of active users."""
    totalJoinedUsers: int
    """The total number of joined users."""
    hideFromListing: bool
    """Whether the session is hidden from listing."""
    dataModelAssemblies: List[DataModelAssemblies]
    """Data model assemblies."""
    universeId: Optional[str] = None
    """The universe id of the session."""
    awayKickEnabled: bool
    awayKickMinutes: int


@resonite_class
class PublicRSAKey:
    """ Data class representing a public RSA key.
    """

    Exponent: str
    """The exponent of the RSA key."""
    Modulus: str
    """The modulus of the RSA key."""


class OnlineStatus(UnknownEnumMixin, Enum):
    """ Enum representing the online status of a Resonite user.
    """

    ONLINE = "Online"
    AWAY = "Away"
    BUSY = "Busy"
    OFFLINE = "Offline"
    UNKNOWN = "__unknown__"


@resonite_class
class UserStatusData:
    """ Data class representing an user status data.
    """

    activeSessions: Optional[List[ResoniteSession]] = None
    """The list of active sessions."""
    currentSession: Optional[ResoniteSession] = None
    """The current session."""
    compatibilityHash: Optional[str] = None
    """The compatibility hash."""
    currentHosting: bool
    """Whether the user is currently hosting a session."""
    currentSessionAccessLevel: CurrentResoniteSessionAccessLevel
    """The access level of the current session."""
    currentSessionHidden: bool
    """Whether the current session is hidden."""
    currentSessionId: Optional[str] = None
    """The ID of the current session."""
    isMobile: bool
    """Whether the user is on a mobile device."""
    lastStatusChange: datetime
    """The timestamp of the last status change."""
    neosVersion: Optional[str] = None
    """The version of Neos."""
    onlineStatus: OnlineStatus
    """The online status of the user."""
    OutputDevice: Optional[str] = None
    """The output device of the user."""
    publicRSAKey: Optional[PublicRSAKey] = None
    """The public RSA key of the user."""

@resonite_class
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
    compatibilityHash: Optional[str] = None
    """The compatibility hash."""
    neosVersion: Optional[str] = None
    """The version of Neos. """
    publicRSAKey: Optional[PublicRSAKey] = None
    """The public RSA key."""
    OutputDevice: Optional[str] = None
    """The output device."""
    isMobile: bool
    """Whether the user is on a mobile device."""

class ContactStatus(UnknownEnumMixin, Enum):
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
    UNKNOWN = "__unknown__"


@resonite_class
class ResoniteContact:
    id: str
    contactUsername: str
    contactStatus: ContactStatus
    isAccepted: bool
    profile: Optional[ProfileData] = None
    latestMessageTime: datetime
    isMigrated: bool
    isCounterpartMigrated: bool
    ownerId: str
    universeId: Optional[str] = None

class ResoniteMessageType(UnknownEnumMixin, Enum):
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
    UNKNOWN = "__unknown__"


@resonite_class
class ResoniteMessageContentUnknown:
    """ Fallback content for message types this module doesn't know yet.
    """
    raw: str

@resonite_class
class ResoniteMessageContentText:
    content: str

    def __str__(self) -> str:
        return self.content

@resonite_class
class ResoniteMessageContentObject:
    """ Data class representing the content of a Resonite object message.
    """

    id: str
    """The ID of the object."""
    ownerId: str
    """The ID of the object owner."""
    assetUri: str
    """The URI of the object asset."""
    version: Optional[ResoniteRecordVersion] = None
    """The version of the object record."""
    name: str
    """The name of the object."""
    recordType: RecordType
    """The type of the object record."""
    ownerName: Optional[str] = None
    """The name of the object owner."""
    tags: List[str]
    """The tags associated with the object."""
    path: Optional[str] = None
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
    firstPublishTime: Optional[datetime] = None
    """The timestamp of the first publish."""
    isDeleted: Optional[bool] = None
    """Whether the object is deleted."""
    visits: int
    """The number of visits."""
    rating: float
    """The rating of the object."""
    randomOrder: int
    """The random order of the object."""
    submissions: Optional[str] = None
    """The submissions of the object."""

@resonite_class
class ResoniteMessageContentSessionInvite:
    name: str
    description: Optional[str] = None
    correspondingWorldId: Optional[WorldId] = None
    tags: List[str]
    sessionId: str
    normalizedSessionId: str
    hostMachineId: str
    hostUsername: str
    hostUserId: Optional[str] = None
    hostUserSessionId: Optional[str] = None
    compatibilityHash: Optional[str] = None
    universeId: Optional[str] = None
    appVersion: Optional[str] = None
    headlessHost: Optional[bool] = None
    sessionURLs: List[str]
    thumbnailUrl: Optional[str] = None
    parentSessionIds: Optional[List[str]] = None
    nestedSessionIds: Optional[List[str]] = None
    sessionUsers: List[ResoniteSessionUser]
    thumbnail: Optional[str] = None
    joinedUsers: int
    activeUsers: int
    totalActiveUsers: int
    totalJoinedUsers: int
    maxUsers: int
    mobileFriendly: bool
    sessionBeginTime: datetime
    lastUpdate: datetime
    accessLevel: CurrentResoniteSessionAccessLevel
    broadcastKey: Optional[str] = None
    dataModelAssemblies: List[DataModelAssemblies]
    hideFromListing: bool
    systemCompatibilityHash: str
    awayKickEnabled: bool
    awayKickMinutes: int
    HasEnded: bool
    IsValid: bool

@resonite_class
class ResoniteMessageContentRequestInvite:
    inviteRequestId: str
    userIdToInvite: str
    usernameToInvite: str
    requestingFromUserId: str
    requestingFromUsername: str
    forSessionId: Optional[str] = None
    forSessionName: Optional[str] = None
    isContactOfHost: Optional[str] = None
    response: Optional[str] = None
    invite: Optional[dict] = None

@resonite_class
class ResoniteMessageContentSound:
    id: str
    ownerId: Optional[str] = None
    assetUri: str
    globalVersion: Optional[int] = None
    localVersion: Optional[int] = None
    lastModifyingUserId: Optional[str] = None
    lastModifyingMachineId: Optional[str] = None
    name: str
    recordType: RecordType
    ownerName: Optional[str] = None
    tags: List[str]
    path: Optional[str] = None
    isPublic: bool
    isForPatrons: Optional[bool] = None
    isListed: bool
    lastModificationTime: datetime
    creationTime: datetime
    firstPublishTime: Optional[datetime] = None
    visits: int
    rating: float
    randomOrder: int
    submissions: Optional[str] = None
    neosDBmanifest: Optional[list] = None
    assetManifest: List[ResoniteAssetManifestEntry]
    isForPatrons: bool
    version: ResoniteRecordVersion
    isDeleted: bool
    isReadOnly: Optional[bool] = None
    description: Optional[str] = None
    thumbnailUri: Optional[str] = None
    rootRecordId: Optional[int] = None
    migrationMetadata: Optional[str] = None
    IsValidOwnerId: bool
    IsValidRecordId: bool



@resonite_class
class ResoniteMessage:
    """Representation of a Resonite message."""
    id: str
    senderId: str
    ownerId: str
    """The ownerId of a ResoniteMessage should start with `U-`"""
    sendTime: str
    recipientId: str
    messageType: ResoniteMessageType
    senderUserSessionId: Optional[str] = None
    isMigrated: bool
    readTime: Optional[datetime] = None
    otherId: Optional[str] = None
    lastUpdateTime: datetime
    description: Optional[str] = None
    content: Optional[
        ResoniteMessageContentText
        | ResoniteMessageContentSessionInvite
        | ResoniteMessageContentRequestInvite
        | ResoniteMessageContentObject
        | ResoniteMessageContentSound
        | ResoniteMessageContentUnknown
    ] = None

    @model_validator(mode='before')
    @classmethod
    def _parse_content(cls, data):
        if isinstance(data, dict) and isinstance(data.get('content'), str):
            raw = data['content']
            mtype = data.get('messageType')
            if mtype == 'Text':
                data = {**data, 'content': {'content': raw}}
            elif mtype in ('SessionInvite', 'InviteRequest', 'Object', 'Sound'):
                data = {**data, 'content': json.loads(raw)}
            else:
                data = {**data, 'content': {'raw': raw}}
        return data

@resonite_class
class ResoniteCloudVar:
    """Representation of Resonite clound variable."""
    ownerId: str
    """The ownerId of a ResoniteCloudVar should start with `U-`"""
    path: str
    """The path of a ResoniteCloudVar should start with a `U-` for a user owned path and a `G-` for a group owned path."""
    value: Optional[str] = None
    partitionKey: str
    rowKey: str
    timestamp: Optional[str] = None
    eTag: Optional[str] = None


class OwnerType(UnknownEnumMixin, Enum):
    MACHINE = "Machine"
    USER = "User"
    GROUP = "Group"
    INVALID = "Invalid"
    UNKNOWN = "__unknown__"


@resonite_class
class ResoniteCloudVarDefs:
    definitionOwnerId: str
    subpath: str
    variableType: str
    defaultValue: Optional[str] = None
    deleteScheduled: bool
    readPermissions: List[str]
    writePermissions: List[str]
    listPermissions: List[str]
    partitionKey: str
    rowKey: str
    timestamp: str
    eTag: str


@resonite_class
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
    studioNameLong: str
    studioNameShort: str
    wiki: str

@resonite_class
class ResoniteBadge:
    tag: str
    url: str
    slotName: str