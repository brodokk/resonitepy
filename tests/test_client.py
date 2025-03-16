import warnings
from copy import deepcopy
from unittest.mock import patch, MagicMock
from datetime import datetime
from dateutil import parser
from urllib.parse import ParseResult

import pytest

from resonitepy.client import Client
from resonitepy.classes import (
    LoginDetails,
    LoginDetailsAuth,
    ResoniteRecord,
    ResoniteObject,
    ResoniteLink,
    ResoniteDirectory,
    ResoniteWorld,
    ResoniteTexture,
    ResoniteAudio,
    ResoniteRecordVersion,
    RecordType,
    ResoniteUserEntitlementExitMessage,
    ResoniteUserEntitlementStorageSpace,
    ResoniteUserEntitlementCredits,
    ResoniteEntitlementDeleteRecovery,
    ResoniteUserEntitlementHeadless,
    ResoniteUserEntitlementBadge,
    ResoniteUserEntitlementBadge,
    ResoniteUserEntitlementGroupCreation,
    supporterMetadataPatreon,
    supporterMetadataStripe,
)

@pytest.fixture
def client():
    return Client()

# def test_login_success(client, mocker):
#     mock_response = {
#         "entity": {
#             "userId": "U-123",
#             "token": "test-token",
#             "secretMachineIdHash": "hash",
#             "secretMachineIdSalt": "salt",
#             "expire": "2023-12-31T23:29:29Z"
#         }
#     }

#     mocker.patch.object(client, 'request', return_value=mock_response)

#     login_details = LoginDetails(
#         username="testuser",
#         authentication=LoginDetailsAuth(password="testpass")
#     )
#     client.login(login_details)

#     assert client.userId == "U-123"
#     assert client.token == "test-token"
#     assert client.secretMachineIdHash == "hash"
#     assert client.secretMachineIdSalt == "salt"

# def test_login_failure(client, mocker):
#     mocker.patch.object(client, 'request', return_value=None)

#     login_details = LoginDetails(
#         username="testuser",
#         authentication=LoginDetailsAuth(password="testpass")
#     )

#     with pytest.raises(Exception, match="Login failed - empty response"):
#         client.login(login_details)

def test_res_db_signature(client):
    res_url = "resrec://U-123/R-456"
    expected_signature = "U-123/R-456"

    result = client.res_db_signature(res_url=res_url)

    assert result == expected_signature

def test_resDBSignature(client, recwarn):
    res_url = "resrec://U-123/R-456"
    expected_signature = "U-123/R-456"

    result = client.resDBSignature(resUrl=res_url)

    assert result == expected_signature

    # Check that DeprecationWarning was raised
    assert len(recwarn) == 1
    assert issubclass(recwarn[0].category, DeprecationWarning)
    assert "resDBSignature is deprecated; please use res_db_signature instead." == str(recwarn[0].message)

def test_db_to_http(client):
    res_url = "resrec://U-123/R-456"
    expected_http_url = "https://assets.resonite.com/U-123/R-456"

    result = client.res_db_to_http(res_url=res_url)

    assert result == expected_http_url

def test_resDbToHttp(client, recwarn):
    res_url = "resrec://U-123/R-456"
    expected_http_url = "https://assets.resonite.com/U-123/R-456"

    result = client.resDbToHttp(resUrl=res_url)

    assert result == expected_http_url

    # Check that DeprecationWarning was raised
    assert len(recwarn) == 1
    assert issubclass(recwarn[0].category, DeprecationWarning)
    assert "resDbToHttp is deprecated; please use res_db_to_http instead." == str(recwarn[0].message)

def test_process_record_ist(client):
    # TODO: Use a more test data
    resonite_record_version = {
        "globalVersion": 42,
        "localVersion": 42,
        "lastModifyingUserId": "U-foxxie",
        "lastModifyingMachineId": "g13a8esw4"
    }
    basic_resonite_record_data = {
        "id": "456",
        "assetUri": "resrec://U-123/R-456", # TODO: verify value
        "version": resonite_record_version,
        "name": "Foxxie",
        "ownerName": "foxxie",
        "path": "U-123/R-456", # TODO: verify value
        "thumbnailUri": "resrec://U-123/R-456", # TODO: verify value
        "isPublic": False,
        "isForPatrons": False,
        "isListed": False,
        "isDeleted": False,
        "tags": ["avatar"],
        "creationTime": "2025-01-01T00:00:01Z",
        "lastModificationTime": "2025-01-01T00:00:01Z",
        "randomOrder": 0,
        "visits": 42,
        "rating": 0,
        "ownerId": "U-foxxie",
        "isReadOnly": False,
    }

    resonite_object_data = deepcopy(basic_resonite_record_data)
    resonite_object_data.update({
        "recordType": "object",
        "lastModifyingMachineId": "g13a8esw4"
    })

    resonite_link_data = deepcopy(basic_resonite_record_data)
    resonite_link_data.update({
        "recordType": "link",
        "assetUri": "resrec://U-123/R-456", # TODO: verify value
    })

    resonite_directory_data = deepcopy(basic_resonite_record_data)
    resonite_directory_data.update({
        "recordType": "directory",
        "lastModifyingMachineId": "g13a8esw4",
        "ownerName": "U-foxxie",
        "tags": ["avatar"],
        "creationTime": "2025-01-01T00:00:01Z",
    })

    resonite_world_data = deepcopy(basic_resonite_record_data)
    resonite_world_data.update({
        "recordType": "world",
    })

    resonite_texture_data = deepcopy(basic_resonite_record_data)
    resonite_texture_data.update({
        "recordType": "texture",
    })

    resonite_audio_data = deepcopy(basic_resonite_record_data)
    resonite_audio_data.update({
        "recordType": "audio",
    })

    precessed_data = [
        resonite_object_data,
        resonite_link_data,
        resonite_directory_data,
        resonite_world_data,
        resonite_texture_data,
        resonite_audio_data,
    ]

    expected_resonite_record = ResoniteObject(**resonite_object_data)
    expected_resonite_record.version = ResoniteRecordVersion(
        **resonite_record_version,
    )
    expected_resonite_record.recordType = RecordType.OBJECT
    expected_resonite_record.creationTime = parser.parse("2025-01-01T00:00:01Z")
    expected_resonite_record.lastModificationTime = parser.parse("2025-01-01T00:00:01Z")

    expected_resonite_link = ResoniteLink(**resonite_link_data)
    expected_resonite_link.version = ResoniteRecordVersion(
        **resonite_record_version,
    )
    expected_resonite_link.recordType = RecordType.LINK
    expected_resonite_link.creationTime = parser.parse("2025-01-01T00:00:01Z")
    expected_resonite_link.lastModificationTime = parser.parse("2025-01-01T00:00:01Z")
    expected_resonite_link.assetUri = ParseResult(scheme='resrec', netloc='U-123', path='/R-456', params='', query='', fragment='')

    expected_resonite_directory = ResoniteDirectory(**resonite_directory_data)
    expected_resonite_directory.version = ResoniteRecordVersion(
        **resonite_record_version,
    )
    expected_resonite_directory.recordType = RecordType.DIRECTORY
    expected_resonite_directory.creationTime = parser.parse("2025-01-01T00:00:01Z")
    expected_resonite_directory.lastModificationTime = parser.parse("2025-01-01T00:00:01Z")

    expected_resonite_world = ResoniteWorld(**resonite_world_data)
    expected_resonite_world.version = ResoniteRecordVersion(
        **resonite_record_version,
    )
    expected_resonite_world.recordType = RecordType.WORLD
    expected_resonite_world.creationTime = parser.parse("2025-01-01T00:00:01Z")
    expected_resonite_world.lastModificationTime = parser.parse("2025-01-01T00:00:01Z")

    expected_texture_record = ResoniteTexture(**resonite_texture_data)
    expected_texture_record.version = ResoniteRecordVersion(
        **resonite_record_version,
    )
    expected_texture_record.recordType = RecordType.TEXTURE
    expected_texture_record.creationTime = parser.parse("2025-01-01T00:00:01Z")
    expected_texture_record.lastModificationTime = parser.parse("2025-01-01T00:00:01Z")

    expected_audio_record = ResoniteAudio(**resonite_audio_data)
    expected_audio_record.version = ResoniteRecordVersion(
        **resonite_record_version,
    )
    expected_audio_record.recordType = RecordType.AUDIO
    expected_audio_record.creationTime = parser.parse("2025-01-01T00:00:01Z")
    expected_audio_record.lastModificationTime = parser.parse("2025-01-01T00:00:01Z")

    expected_data = [
        expected_resonite_record,
        expected_resonite_link,
        expected_resonite_directory,
        expected_resonite_world,
        expected_texture_record,
        expected_audio_record,
    ]

    result = client.process_record_ist(data=precessed_data)

    assert result == expected_data

def test_processRecordList(client, recwarn):

    resonite_record_version = {
        "globalVersion": 42,
        "localVersion": 42,
        "lastModifyingUserId": "U-foxxie",
        "lastModifyingMachineId": "g13a8esw4"
    }
    basic_resonite_record_data = {
        "id": "456",
        "assetUri": "resrec://U-123/R-456", # TODO: verify value
        "version": resonite_record_version,
        "name": "Foxxie",
        "ownerName": "foxxie",
        "path": "U-123/R-456", # TODO: verify value
        "thumbnailUri": "resrec://U-123/R-456", # TODO: verify value
        "isPublic": False,
        "isForPatrons": False,
        "isListed": False,
        "isDeleted": False,
        "tags": ["avatar"],
        "creationTime": "2025-01-01T00:00:01Z",
        "lastModificationTime": "2025-01-01T00:00:01Z",
        "randomOrder": 0,
        "visits": 42,
        "rating": 0,
        "ownerId": "U-foxxie",
        "isReadOnly": False,
    }

    resonite_object_data = deepcopy(basic_resonite_record_data)
    resonite_object_data.update({
        "recordType": "object",
        "lastModifyingMachineId": "g13a8esw4"
    })

    precessed_data = [resonite_object_data]

    expected_resonite_record = ResoniteObject(**resonite_object_data)
    expected_resonite_record.version = ResoniteRecordVersion(
        **resonite_record_version,
    )
    expected_resonite_record.recordType = RecordType.OBJECT
    expected_resonite_record.creationTime = parser.parse("2025-01-01T00:00:01Z")
    expected_resonite_record.lastModificationTime = parser.parse("2025-01-01T00:00:01Z")

    expected_data = [expected_resonite_record]

    result = client.processRecordList(data=precessed_data)

    assert result == expected_data

    # Check that DeprecationWarning was raised
    assert len(recwarn) == 1
    assert issubclass(recwarn[0].category, DeprecationWarning)
    assert "processRecordList is deprecated; please use process_record_ist instead." == str(recwarn[0].message)


def test_to_resonite_user(client):

    user_data = {
        'id': 'U-foxxie',
        'username': 'foxxie',
        'normalizedUsername': 'foxxie',
        'email': 'foxxie@example.com',
        'registrationDate':'2022-09-23T21:01:51.9848632Z',
        'isVerified': True,
        'isLocked': False,
        'supressBanEvasion': False,
        '2fa_login': False,
        'tags': [
            'user'
        ],
        'profile': {
            'iconUrl': 'resdb:///9ece91ae5452731cbafa4ecf43426e363bds45b5679f76430b1456fghnrt78bd9766b32fc4ef.webp', 'displayBadges': []
        },
        'supporterMetadata': [
            {
                '$type': 'patreon',
                'isActiveSupporter': True,
                'isActive': True,
                'totalSupportMonths': 1,
                'totalSupportCents': 1,
                'lastTierCents': 1,
                'highestTierCents': 1,
                'lowestTierCents': 1,
                'firstSupportTimestamp': '2020-09-23T21:12:32.1948324Z',
                'lastSupportTimestamp': '2021-02-28T03:01:51.9589802Z'
            }, {
                '$type': 'stripe'
            }
        ],
        'entitlements': [
            {
                '$type': 'exitMessage',
                'isLifetime': True,
                'messageCount': 40,
                'friendlyDescription': '40 Custom Exit Messages',
                'entitlementOrigins': ['Patreon']
            }, {
                '$type': 'storageSpace',
                'bytes': 536870912000,
                'maximumShareLevel': 'GroupsAndUsers',
                'storageId': 'Patreon-2025-2-28-46968517-1326119',
                'group': 'patreon',
                'startsOn': '2020-02-28T00:00:00Z',
                'expiresOn': '2020-04-04T00:00:00Z',
                'name': 'Patreon',
                'description': 'Additional storage space reward for Patreon supporters',
                'entitlementOrigins': ['Patreon']
            }, {
                '$type': 'credits',
                'creditType': 'Spoken',
                'friendlyDescription': 'Spoken credit in videos/streams or prominent text',
                'entitlementOrigins': ['Patreon']
            },
            {
                '$type': 'deleteRecovery',
                'entitlementOrigins': ['Patreon']
            }, {
                '$type': 'headless',
                'friendlyDescription': 'Headless Server Access (send /headlessCode to Resonite in Contacts list to get the current code)',
                'entitlementOrigins': ['Patreon']
            }, {
                '$type': 'badge',
                'badgeType': 'Static2D',
                'badgeCount': 1,
                'entitlementOrigins': ['Patreon']
            }, {
                '$type': 'badge',
                'badgeType': 'Model',
                'badgeCount': 1,
                'entitlementOrigins': ['Patreon']
            }, {
                '$type': 'groupCreation',
                'groupCount': 2,
                'entitlementOrigins': ['Patreon']
            }
        ],
        'isActiveSupporter': True,
        'migratedData': {
            'username': 'foxxie',
            'email': 'foxxie@example.com',
            'userId': 'U-foxxie',
            'quotaBytes': 161063273600,
            'usedBytes': 34343755330,
            'quotaBytesSources': {
                'base': 1073741824,
                'patreon': 161063273600
            },
            'registrationDate': '2020-12-03T22:33:37.9715713Z',
            'patreonData': {
                'lastPatreonEmail': 'foxxie@example.com',
                'isPatreonSupporter': True,
                'patreonId': '46928000',
                'lastPatreonPledgeCents': 3600,
                'lastTotalCents': 153200,
                'minimumTotalUnits': 0,
                'externalCents': 0,
                'lastExternalCents': 0,
                'hasSupported': True,
                'priorityIssue': 289,
                'lastActivationTime': '2021-09-01T23:44:39.3140424Z',
                'lastPaidPledgeAmount': 3600,
                'snapshots': [
                    {
                        'totalCents': 1,
                        'patreonRawCents': 1,
                        'deltaCents': 0,
                        'pledgeCents': 1,
                        'email': 'foxxie@example.com',
                        'timestamp': '2021-04-08T21:28:45.8411655Z'
                    },
                ]
            }
        }
    }

    excepted_user_data = deepcopy(user_data)

    del excepted_user_data['entitlements'][0]['$type']
    del excepted_user_data['entitlements'][1]['$type']
    del excepted_user_data['entitlements'][2]['$type']
    del excepted_user_data['entitlements'][3]['$type']
    del excepted_user_data['entitlements'][4]['$type']
    del excepted_user_data['entitlements'][5]['$type']
    del excepted_user_data['entitlements'][6]['$type']
    del excepted_user_data['entitlements'][7]['$type']

    del excepted_user_data['supporterMetadata'][0]['$type']
    del excepted_user_data['supporterMetadata'][1]['$type']

    expected_entitlement_exit_message = ResoniteUserEntitlementExitMessage(**excepted_user_data['entitlements'][0])
    expected_entitlement_storage_space = ResoniteUserEntitlementStorageSpace(**excepted_user_data['entitlements'][1])
    expected_entitlement_credits = ResoniteUserEntitlementCredits(**excepted_user_data['entitlements'][2])
    expected_entitlement_delete_recovery = ResoniteEntitlementDeleteRecovery(**excepted_user_data['entitlements'][3])
    expected_entitlement_headless = ResoniteUserEntitlementHeadless(**excepted_user_data['entitlements'][4])
    expected_entitlement_badge_static2d = ResoniteUserEntitlementBadge(**excepted_user_data['entitlements'][5])
    expected_entitlement_badge_model = ResoniteUserEntitlementBadge(**excepted_user_data['entitlements'][6])
    expected_entitlement_group_creation = ResoniteUserEntitlementGroupCreation(**excepted_user_data['entitlements'][7])

    expected_entitlement_storage_space.startsOn = parser.parse(expected_entitlement_storage_space.startsOn)
    expected_entitlement_storage_space.expiresOn = parser.parse(expected_entitlement_storage_space.expiresOn)

    expected_supporter_metadata_patreon = supporterMetadataPatreon(**excepted_user_data['supporterMetadata'][0])
    expected_supporter_metadata_stripe = supporterMetadataStripe(**excepted_user_data['supporterMetadata'][1])

    expected_supporter_metadata_patreon.firstSupportTimestamp = parser.parse(expected_supporter_metadata_patreon.firstSupportTimestamp)
    expected_supporter_metadata_patreon.lastSupportTimestamp = parser.parse(expected_supporter_metadata_patreon.lastSupportTimestamp)

    expected_entitlements = [
        expected_entitlement_exit_message,
        expected_entitlement_storage_space,
        expected_entitlement_credits,
        expected_entitlement_delete_recovery,
        expected_entitlement_headless,
        expected_entitlement_badge_static2d,
        expected_entitlement_badge_model,
        expected_entitlement_group_creation,
    ]

    expected_supporter_metadatas = [
        expected_supporter_metadata_patreon,
        expected_supporter_metadata_stripe,
    ]

    result = client.to_resonite_user(deepcopy(user_data))

    assert result['entitlements'] == expected_entitlements
    assert '2fa_login' not in result
    assert result['two_fa_login'] == user_data['2fa_login']
    assert result['supporterMetadata'] == expected_supporter_metadatas
