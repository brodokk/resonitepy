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
    resrec_url = "resrec://U-123/R-456"
    expected_resrec_signature = "U-123/R-456"

    assert client.res_db_signature(res_url=resrec_url) == expected_resrec_signature

    resdb_url = "resdb:///grs4587f4659696ca9c67edf89ee7g1289rsw5sz478e81gh6rs458.pdf"
    expected_resdb_signature = "grs4587f4659696ca9c67edf89ee7g1289rsw5sz478e81gh6rs458"

    assert client.res_db_signature(res_url=resdb_url) == expected_resdb_signature

def test_resDBSignature(client, recwarn):
    resrec_url = "resrec://U-123/R-456"
    expected_resrec_signature = "U-123/R-456"

    assert client.resDBSignature(resUrl=resrec_url) == expected_resrec_signature

    resdb_url = "resdb:///grs4587f4659696ca9c67edf89ee7g1289rsw5sz478e81gh6rs458.pdf"
    expected_resdb_signature = "grs4587f4659696ca9c67edf89ee7g1289rsw5sz478e81gh6rs458"

    assert client.resDBSignature(resUrl=resdb_url) == expected_resdb_signature

    # Check that DeprecationWarning was raised
    assert len(recwarn) == 2
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

