from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from hsclient.hydroshare import HydroShare, Resource


class FakeResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.content = b""

    def json(self):
        return self._json_data


@pytest.fixture
def mock_session_init():
    """Patches HydroShareSession so HydroShare() doesn't make real network calls."""
    with patch("hsclient.hydroshare.HydroShareSession.get") as mock_get, patch(
        "hsclient.hydroshare.HydroShareSession.post"
    ) as mock_post:
        mock_get.return_value = FakeResponse(200, {"username": "test_user"})
        mock_post.return_value = FakeResponse(201, {"access_key": "AKIATEST", "secret_key": "SECRETTEST"})
        yield mock_get, mock_post


def test_s3_client_initialized_on_login(mock_session_init):
    with patch("hsclient.hydroshare.s3fs") as mock_s3fs:
        mock_s3fs.S3FileSystem.return_value = MagicMock()
        hs = HydroShare(username="test_user", password="test_pass")

        mock_s3fs.S3FileSystem.assert_called_once_with(
            key="AKIATEST",
            secret="SECRETTEST",
            endpoint_url=HydroShare.default_s3_endpoint_url,
            config_kwargs={
                "request_checksum_calculation": "when_required",
                "response_checksum_validation": "when_required",
            },
        )
        assert hs.s3_client is mock_s3fs.S3FileSystem.return_value


def test_s3_client_is_none_when_credential_fetch_fails(mock_session_init):
    _, mock_post = mock_session_init
    mock_post.side_effect = Exception("Failed POST, status_code 500")

    with patch("hsclient.hydroshare.s3fs") as mock_s3fs:
        # login should not raise even though S3 credential retrieval failed
        hs = HydroShare(username="test_user", password="test_pass")
        assert hs.s3_client is None
        mock_s3fs.S3FileSystem.assert_not_called()


def test_s3_client_is_none_without_credentials(mock_session_init):
    """No username/password supplied -> no S3 bootstrap attempted at all."""
    with patch("hsclient.hydroshare.s3fs") as mock_s3fs:
        hs = HydroShare()
        assert hs.s3_client is None
        mock_s3fs.S3FileSystem.assert_not_called()


@pytest.fixture
def resource_with_s3():
    mock_s3_client = MagicMock()
    resource = Resource(map_path="/resource/abc123/data/resourcemap.xml", hs_session=MagicMock(), s3_client=mock_s3_client)
    resource._parsed_s3_bucket_path = "test-bucket/abc123/data/contents"
    return resource, mock_s3_client


@pytest.fixture
def resource_without_s3():
    resource = Resource(map_path="/resource/abc123/data/resourcemap.xml", hs_session=MagicMock(), s3_client=None)
    return resource


def test_build_s3_path_raises_without_s3_client(resource_without_s3):
    with pytest.raises(Exception):
        resource_without_s3._build_s3_path("some/file.txt")


def test_build_s3_path_builds_expected_path(resource_with_s3):
    resource, _ = resource_with_s3
    assert resource._build_s3_path("some/file.txt") == "test-bucket/abc123/data/contents/some/file.txt"
    assert resource._build_s3_path() == "test-bucket/abc123/data/contents"


def test_s3_bucket_path_discovered_via_rest(mock_session_init):
    with patch.object(Resource, "resource_id", new_callable=PropertyMock) as mock_resource_id:
        mock_resource_id.return_value = "abc123"
        mock_hs_session = MagicMock()
        mock_hs_session.get.return_value = FakeResponse(
            200, {"bucket": "test-bucket", "prefix": "abc123/data/contents"}
        )
        resource = Resource(map_path="x", hs_session=mock_hs_session, s3_client=MagicMock())

        assert resource.s3_bucket_path == "test-bucket/abc123/data/contents"
        mock_hs_session.get.assert_called_once_with("/hsapi/resource/s3/abc123/", status_code=200)

        # cached on second access
        resource.s3_bucket_path
        mock_hs_session.get.assert_called_once()


def test_s3_list_objects_files_only_non_recursive(resource_with_s3):
    resource, mock_s3_client = resource_with_s3
    mock_s3_client.ls.return_value = [
        {"name": "test-bucket/abc123/data/contents", "type": "directory"},
        {"name": "test-bucket/abc123/data/contents/file1.txt", "type": "file"},
        {"name": "test-bucket/abc123/data/contents/subfolder", "type": "directory"},
    ]

    result = resource.s3_list_objects(include_folders=False)

    mock_s3_client.ls.assert_called_once_with("test-bucket/abc123/data/contents", detail=True)
    assert result == ["file1.txt"]


def test_s3_list_objects_files_and_folders_non_recursive(resource_with_s3):
    resource, mock_s3_client = resource_with_s3
    mock_s3_client.ls.return_value = [
        {"name": "test-bucket/abc123/data/contents", "type": "directory"},
        {"name": "test-bucket/abc123/data/contents/file1.txt", "type": "file"},
        {"name": "test-bucket/abc123/data/contents/subfolder", "type": "directory"},
    ]

    result = resource.s3_list_objects(include_folders=True)

    mock_s3_client.ls.assert_called_once_with("test-bucket/abc123/data/contents", detail=True)
    assert result == ["file1.txt", "subfolder"]


def test_s3_list_objects_files_only_recursive(resource_with_s3):
    resource, mock_s3_client = resource_with_s3
    mock_s3_client.find.return_value = [
        "test-bucket/abc123/data/contents/file1.txt",
        "test-bucket/abc123/data/contents/subfolder/file2.txt",
    ]

    result = resource.s3_list_objects(recursive=True, include_folders=False)

    mock_s3_client.find.assert_called_once_with("test-bucket/abc123/data/contents", withdirs=False)
    assert result == ["file1.txt", "subfolder/file2.txt"]


def test_s3_list_objects_files_only_with_folder_path(resource_with_s3):
    resource, mock_s3_client = resource_with_s3
    mock_s3_client.ls.return_value = [{"name": "test-bucket/abc123/data/contents/sub/file1.txt", "type": "file"}]

    result = resource.s3_list_objects(folder_path="sub", include_folders=False)

    mock_s3_client.ls.assert_called_once_with("test-bucket/abc123/data/contents/sub", detail=True)
    assert result == ["sub/file1.txt"]


def test_s3_file_download(resource_with_s3, tmp_path):
    resource, mock_s3_client = resource_with_s3
    mock_s3_client.exists.return_value = True

    result = resource.s3_file_download("some/file.txt", str(tmp_path))

    expected_remote = "test-bucket/abc123/data/contents/some/file.txt"
    mock_s3_client.exists.assert_called_once_with(expected_remote)
    expected_local = str(tmp_path / "file.txt")
    mock_s3_client.get.assert_called_once_with(expected_remote, expected_local)
    assert result == expected_local


def test_s3_file_download_missing_file_raises(resource_with_s3, tmp_path):
    resource, mock_s3_client = resource_with_s3
    mock_s3_client.exists.return_value = False

    with pytest.raises(FileNotFoundError):
        resource.s3_file_download("missing.txt", str(tmp_path))


def test_s3_file_upload(resource_with_s3, tmp_path):
    resource, mock_s3_client = resource_with_s3
    local_file = tmp_path / "upload.txt"
    local_file.write_text("hello")

    result = resource.s3_file_upload(str(local_file))

    mock_s3_client.put.assert_called_once_with(str(local_file), "test-bucket/abc123/data/contents/upload.txt")
    assert result == "upload.txt"


def test_s3_file_upload_with_folder(resource_with_s3, tmp_path):
    resource, mock_s3_client = resource_with_s3
    local_file = tmp_path / "upload.txt"
    local_file.write_text("hello")

    result = resource.s3_file_upload(str(local_file), folder="my/folder")

    mock_s3_client.put.assert_called_once_with(
        str(local_file), "test-bucket/abc123/data/contents/my/folder/upload.txt"
    )
    assert result == "my/folder/upload.txt"


def test_s3_file_upload_missing_local_file_raises(resource_with_s3):
    resource, _ = resource_with_s3
    with pytest.raises(FileNotFoundError):
        resource.s3_file_upload("/nonexistent/path/file.txt")


def test_s3_file_delete(resource_with_s3):
    resource, mock_s3_client = resource_with_s3
    mock_s3_client.exists.return_value = True

    resource.s3_file_delete("some/file.txt")

    expected_remote = "test-bucket/abc123/data/contents/some/file.txt"
    mock_s3_client.exists.assert_called_once_with(expected_remote)
    mock_s3_client.rm.assert_called_once_with(expected_remote)


def test_s3_file_delete_missing_file_raises(resource_with_s3):
    resource, mock_s3_client = resource_with_s3
    mock_s3_client.exists.return_value = False

    with pytest.raises(FileNotFoundError):
        resource.s3_file_delete("missing.txt")

    mock_s3_client.rm.assert_not_called()
