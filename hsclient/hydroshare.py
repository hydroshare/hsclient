import getpass
import os
import sqlite3
import tempfile
import time
from datetime import datetime
from posixpath import basename, dirname, join as urljoin, splitext
from typing import Dict, List, Union
from urllib.parse import urlparse
from urllib.request import pathname2url, url2pathname
from zipfile import ZipFile

import pandas
import requests

from hsclient.schemas import load_rdf, rdf_string
from hsclient.schemas.base_models import BaseMetadata
from hsclient.schemas.enums import AggregationType
from hsclient.schemas.fields import BoxCoverage, PeriodCoverage, PointCoverage
from hsclient.schemas.json_models import ResourcePreview, User
from hsclient.utils import attribute_filter, is_aggregation, main_file_type


class File(str):
    def __new__(cls, value, file_url, checksum):
        return super(File, cls).__new__(cls, value)

    def __init__(self, value, file_url, checksum):
        self._file_url = file_url
        self._checksum = checksum

    @property
    def path(self) -> str:
        return self

    @property
    def name(self) -> str:
        return basename(self)

    @property
    def extension(self) -> str:
        return splitext(self.name)[1]

    @property
    def folder(self) -> str:
        return dirname(self)

    @property
    def checksum(self):
        return self._checksum

    @property
    def url(self):
        return self._file_url


class Aggregation:
    def __init__(self, map_path, hs_session, checksums=None):
        self._map_path = map_path
        self._hs_session = hs_session
        self._retrieved_map = None
        self._retrieved_metadata = None
        self._parsed_files = None
        self._parsed_aggregations = None
        self._parsed_checksums = checksums

    def __str__(self):
        return self._map_path

    @property
    def _map(self):
        if not self._retrieved_map:
            self._retrieved_map = self._retrieve_and_parse(self._map_path)
        return self._retrieved_map

    @property
    def _metadata(self):
        if not self._retrieved_metadata:
            self._retrieved_metadata = self._retrieve_and_parse(self.metadata_path)
        return self._retrieved_metadata

    @property
    def _checksums(self):
        if not self._parsed_checksums:
            self._parsed_checksums = self._retrieve_checksums(self._checksums_path)
        return self._parsed_checksums

    @property
    def _files(self):
        if not self._parsed_files:
            self._parsed_files = []
            for file in self._map.describes.files:
                if not is_aggregation(str(file.path)):
                    if not file.path == self.metadata_path:
                        if not str(file.path).endswith('/'):  # checking for folders, shouldn't have to do this
                            file_checksum_path = file.path.split(self._resource_path, 1)[1].strip("/")
                            file_path = url2pathname(
                                file_checksum_path.split(
                                    "data/contents/",
                                )[1]
                            )
                            # f = File(file_path, url2pathname(file.path), self._checksums[file_checksum_path])
                            f = File(file_path, url2pathname(file.path), None)
                            self._parsed_files.append(f)
        return self._parsed_files

    @property
    def _aggregations(self):
        if not self._parsed_aggregations:
            self._parsed_aggregations = []
            for file in self._map.describes.files:
                if is_aggregation(str(file.path)):
                    # self._parsed_aggregations.append(Aggregation(url2pathname(file.path), self._hs_session, self._checksums))
                    self._parsed_aggregations.append(Aggregation(url2pathname(file.path), self._hs_session, None))
        return self._parsed_aggregations

    @property
    def _checksums_path(self):
        path = self.metadata_path.split("/data/", 1)[0]
        path = urljoin(path, "manifest-md5.txt")
        return path

    @property
    def _hsapi_path(self):
        resource_path = self._resource_path
        hsapi_path = urljoin("hsapi", resource_path)
        return hsapi_path

    @property
    def _resource_path(self):
        resource_path = self.metadata_path[: len("/resource/b4ce17c17c654a5c8004af73f2df87ab/")].strip("/")
        return resource_path

    def _retrieve_and_parse(self, path):
        file_str = self._hs_session.retrieve_string(path)
        instance = load_rdf(file_str)
        return instance

    def _retrieve_checksums(self, path):
        file_str = self._hs_session.retrieve_string(path)
        data = {
            pathname2url(path): checksum
            for checksum, path in (line.split("    ") for line in file_str.split("\n") if line)
        }
        return data

    def _download(self, save_path: str = "", unzip_to: str = None) -> str:
        main_file_path = self.main_file_path

        path = urljoin(self._resource_path, "data", "contents", main_file_path)
        params = {"zipped": "true", "aggregation": "true"}
        path = path.replace('resource', 'django_irods/rest_download', 1)
        downloaded_zip = self._hs_session.retrieve_zip(path, save_path=save_path, params=params)

        if unzip_to:
            import zipfile

            with zipfile.ZipFile(downloaded_zip, 'r') as zip_ref:
                zip_ref.extractall(unzip_to)
                os.remove(downloaded_zip)
            return unzip_to
        return downloaded_zip

    @property
    def metadata_file(self):
        return self.metadata_path.split("/data/contents/", 1)[1]

    @property
    def metadata(self) -> BaseMetadata:
        return self._metadata

    @property
    def metadata_path(self) -> str:
        return urlparse(str(self._map.describes.is_documented_by)).path

    @property
    def main_file_path(self) -> str:
        mft = main_file_type(self.metadata.type)
        if mft:
            for file in self.files():
                if str(file).endswith(mft):
                    return file.path
        if self.metadata.type == AggregationType.FileSetAggregation:
            return self.files()[0].folder
        return self.files()[0].path

    def save(self) -> None:
        metadata_file = self.metadata_file
        metadata_string = rdf_string(self._retrieved_metadata, rdf_format="xml")
        url = urljoin(self._hsapi_path, "ingest_metadata")
        self._hs_session.upload_file(url, files={'file': (metadata_file, metadata_string)})
        self.refresh()

    def files(self, search_aggregations=False, **kwargs) -> List[File]:
        files = self._files
        for key, value in kwargs.items():
            files = list(filter(lambda file: attribute_filter(file, key, value), files))
        if search_aggregations:
            for aggregation in self.aggregations():
                files = files + list(aggregation.files(search_aggregations=search_aggregations, **kwargs))
        return files

    def file(self, search_aggregations=False, **kwargs) -> File:
        files = self.files(search_aggregations=search_aggregations, **kwargs)
        if files:
            return files[0]
        return None

    def aggregations(self, **kwargs) -> List[BaseMetadata]:
        aggregations = self._aggregations
        for key, value in kwargs.items():
            if key.startswith('file__'):
                file_args = {key[len('file__') :]: value}
                aggregations = [agg for agg in aggregations if agg.files(**file_args)]
            elif key.startswith('files__'):
                file_args = {key[len('files__') :]: value}
                aggregations = [agg for agg in aggregations if agg.files(**file_args)]
            else:
                aggregations = filter(lambda agg: attribute_filter(agg.metadata, key, value), aggregations)
        return list(aggregations)

    def aggregation(self, **kwargs) -> BaseMetadata:
        aggregations = self.aggregations(**kwargs)
        if aggregations:
            return aggregations[0]
        return None

    def refresh(self) -> None:
        # TODO, refresh should destroy the aggregation objects and async fetch everything.
        self._retrieved_map = None
        self._retrieved_metadata = None
        self._parsed_files = None
        self._parsed_aggregations = None
        self._parsed_checksums = None

    def as_series(self, series_id: str, agg_path: str = None) -> Dict[int, pandas.Series]:
        def to_series(timeseries_file: str):
            con = sqlite3.connect(timeseries_file)
            return pandas.read_sql(
                f'SELECT * FROM TimeSeriesResultValues WHERE ResultID IN '
                f'(SELECT ResultID FROM Results WHERE ResultUUID = "{series_id}");',
                con,
            ).squeeze()

        if agg_path is None:
            with tempfile.TemporaryDirectory() as td:
                self._download(unzip_to=td)
                # zip extracted to folder with main file name
                file_name = self.file(extension=".sqlite").name
                return to_series(urljoin(td, file_name, file_name))
        return to_series(urljoin(agg_path, self.file(extension=".sqlite").name))


class Resource(Aggregation):
    @property
    def _hsapi_path(self):
        path = urlparse(self.metadata.identifier).path
        return '/hsapi' + path

    def _upload(self, file, destination_path):
        path = urljoin(self._hsapi_path, "files", destination_path.strip("/"))
        self._hs_session.upload_file(path, files={'file': open(file, 'rb')}, status_code=201)

    def _delete_file(self, path) -> None:
        path = urljoin(self._hsapi_path, "files", path)
        self._hs_session.delete(path, status_code=200)

    def _download_file_folder(self, path: str, save_path: str) -> None:
        return self._hs_session.retrieve_zip(path, save_path)

    def _delete_file_folder(self, path: str) -> None:
        path = urljoin(self._hsapi_path, "folders", path)
        self._hs_session.delete(path, status_code=200)

    # system information

    @property
    def resource_id(self) -> str:
        return self._map.identifier

    def system_metadata(self):
        hsapi_path = urljoin(self._hsapi_path, 'sysmeta')
        return self._hs_session.get(hsapi_path, status_code=200).json()

    # access operations

    def access_rules(self, public: bool):
        url = urljoin(self._hsapi_path, "access")
        raise NotImplementedError("TODO")

    @property
    def access_permission(self):
        path = urljoin(self._hsapi_path, "access")
        response = self._hs_session.get(path, status_code=200)
        return response.json()

    # resource operations

    def download(self, save_path: str = "") -> str:
        return self._hs_session.retrieve_bag(self._hsapi_path, save_path=save_path)

    def delete(self) -> None:
        """"""
        hsapi_path = self._hsapi_path
        self._hs_session.delete(hsapi_path, status_code=204)
        self.refresh()
        self.refresh()

    def save(self) -> None:
        metadata_string = rdf_string(self._retrieved_metadata, rdf_format="xml")
        path = urljoin(self._hsapi_path, "ingest_metadata")
        self._hs_session.upload_file(path, files={'file': ('resourcemetadata.xml', metadata_string)})
        self.refresh()

    # referenced content operations

    def reference_create(self, file_name: str, url: str, path: str = '') -> None:
        request_path = urljoin(self._hsapi_path.replace(self.resource_id, ""), "data-store-add-reference")
        self._hs_session.post(
            request_path,
            data={"res_id": self.resource_id, "curr_path": path, "ref_name": file_name, "ref_url": url},
            status_code=200,
        )
        self.refresh()

    def reference_update(self, file_name: str, url: str, path: str = '') -> None:
        request_path = urljoin(self._hsapi_path.replace(self.resource_id, ""), "data_store_edit_reference_url")
        self._hs_session.post(
            request_path,
            data={"res_id": self.resource_id, "curr_path": path, "url_filename": file_name, "new_ref_url": url},
            status_code=200,
        )
        self.refresh()

    # file operations

    def folder_create(self, folder: str) -> None:
        path = urljoin(self._hsapi_path, "folders", folder)
        self._hs_session.put(path, status_code=201)

    def folder_rename(self, path: str, new_path: str) -> None:
        self.file_rename(path=path, new_path=new_path)

    def folder_delete(self, path: str = None) -> None:
        self._delete_file_folder(path)
        self.refresh()

    def folder_download(self, *paths: str, save_path: str = "", zipped: bool = False):
        if len(paths) > 1:
            raise NotImplementedError(
                "Currently may only download one folder at a time, hydroshare needs to be updated to allow for more"
            )
        path = paths[0]
        return self._hs_session.retrieve_zip(
            urljoin(self._resource_path, "data", "contents", path), save_path, params={"zipped": "true"}
        )

    def file_download(self, *paths: str, save_path: str = "", zipped: bool = False):
        if len(paths) > 1:
            raise NotImplementedError(
                "Currently may only download one file at a time, hydroshare needs to be updated to allow for more"
            )
        path = paths[0]
        if zipped:
            return self._hs_session.retrieve_zip(
                urljoin(self._resource_path, "data", "contents", path), save_path, params={"zipped": "true"}
            )
        else:
            return self._hs_session.retrieve_file(urljoin(self._resource_path, "data", "contents", path), save_path)

    def file_delete(self, path: str = None) -> None:
        self._delete_file(path)
        self.refresh()

    def file_rename(self, path: str, new_path: str) -> None:
        rename_path = urljoin(self._hsapi_path, "functions", "move-or-rename")
        self._hs_session.post(rename_path, status_code=200, data={"source_path": path, "target_path": new_path})
        self.refresh()

    def file_zip(self, path: str, zip_name: str = None, remove_files: bool = True) -> None:
        zip_name = basename(path) + ".zip" if not zip_name else zip_name
        data = {"input_coll_path": path, "output_zip_file_name": zip_name, "remove_original_after_zip": remove_files}
        zip_path = urljoin(self._hsapi_path, "functions", "zip")
        self._hs_session.post(zip_path, status_code=200, data=data)
        self.refresh()

    def file_unzip(self, path: str) -> None:
        if not path.endswith(".zip"):
            raise Exception("File {} is not a zip, and cannot be unzipped".format(path))
        unzip_path = urljoin(self._hsapi_path, "functions", "unzip", "data", "contents", path)
        self._hs_session.post(unzip_path, status_code=200, data={"overwrite": "true", "ingest_metadata": "true"})
        self.refresh()

    def file_aggregate(self, path, agg_type: AggregationType) -> None:
        type_value = agg_type.value
        data = {}
        if agg_type == AggregationType.SingleFileAggregation:
            type_value = 'SingleFile'
        if agg_type == AggregationType.FileSetAggregation:
            relative_path = dirname(path)
            data = {"folder_path": relative_path}

        url = urljoin(self._hsapi_path, "functions", "set-file-type", path, type_value)
        self._hs_session.post(url, status_code=201, data=data)
        self.refresh()
        return self.aggregation(file__path=path)

    def file_upload(self, *files: str, destination_path: str = "") -> None:
        if len(files) == 1:
            self._upload(files[0], destination_path=destination_path)
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                zipped_file = urljoin(tmpdir, 'files.zip')
                with ZipFile(urljoin(tmpdir, zipped_file), 'w') as zipped:
                    for file in files:
                        zipped.write(file, basename(file))
                self._upload(zipped_file, destination_path=destination_path)
                unzip_path = urljoin(
                    self._hsapi_path, "functions", "unzip", "data", "contents", destination_path, 'files.zip'
                )
                self._hs_session.post(
                    unzip_path, status_code=200, data={"overwrite": "true", "ingest_metadata": "true"}
                )
        self.refresh()
        # TODO, return those files?

    # aggregation operations

    def aggregation_remove(self, aggregation: Aggregation) -> None:
        path = urljoin(
            aggregation._hsapi_path,
            "functions",
            "remove-file-type",
            aggregation.metadata.type.value + "LogicalFile",
            aggregation.main_file_path,
        )
        aggregation._hs_session.post(path, status_code=200)
        aggregation.refresh()
        self.refresh()

    def aggregation_delete(self, aggregation: Aggregation) -> None:
        path = urljoin(
            aggregation._hsapi_path,
            "functions",
            "delete-file-type",
            aggregation.metadata.type.value + "LogicalFile",
            aggregation.main_file_path,
        )
        aggregation._hs_session.delete(path, status_code=200)
        aggregation.refresh()
        self.refresh()

    def aggregation_download(self, aggregation: Aggregation, save_path: str = "", unzip_to: str = None) -> str:
        return aggregation._download(save_path=save_path, unzip_to=unzip_to)


class HydroShareSession:
    def __init__(self, username, password, host, protocol, port):
        self._session = requests.Session()
        self.set_auth((username, password))
        self._host = host
        self._protocol = protocol
        self._port = port

    def set_auth(self, auth):
        self._session.auth = auth

    @property
    def host(self):
        return self._host

    @property
    def base_url(self):
        return "{}://{}:{}".format(self._protocol, self._host, self._port)

    def _build_url(self, path: str):
        path = "/" + path.strip("/") + "/"
        return self.base_url + path

    def retrieve_string(self, path):
        file = self.get(path, status_code=200, allow_redirects=True)
        return file.content.decode()

    def retrieve_file(self, path, save_path=""):
        file = self.get(path, status_code=200, allow_redirects=True)

        cd = file.headers['content-disposition']
        filename = cd.split("filename=")[1].strip('"')
        downloaded_file = urljoin(save_path, filename)
        with open(downloaded_file, 'wb') as f:
            f.write(file.content)
        return downloaded_file

    def retrieve_bag(self, path, save_path=""):
        file = self.get(path, status_code=200, allow_redirects=True)

        if file.headers['Content-Type'] != "application/zip":
            time.sleep(1)
            return self.retrieve_bag(path, save_path)
        return self.retrieve_file(path, save_path)

    def check_task(self, task_id):
        response = self.get(f"/hsapi/taskstatus/{task_id}/", status_code=200)
        return response.json()['status']

    def retrieve_zip(self, path, save_path="", params=None):
        if params is None:
            params = {}
        file = self.get(path, status_code=200, allow_redirects=True, params=params)

        json_response = file.json()
        task_id = json_response['task_id']
        download_path = json_response['download_path']
        zip_status = json_response['zip_status']
        if zip_status == "Not ready":
            while self.check_task(task_id) != 'true':
                time.sleep(1)
        return self.retrieve_file(download_path, save_path)

    def upload_file(self, path, files, status_code=204):
        return self.post(path, files=files, status_code=status_code)

    def post(self, path, status_code, data=None, params={}, **kwargs):
        url = encode_resource_url(self._build_url(path))
        response = self._session.post(url, params=params, data=data, **kwargs)
        if response.status_code != status_code:
            raise Exception(
                "Failed POST {}, status_code {}, message {}".format(url, response.status_code, response.content)
            )
        return response

    def put(self, path, status_code, data=None, **kwargs):
        url = encode_resource_url(self._build_url(path))
        response = self._session.put(url, data=data, **kwargs)
        if response.status_code != status_code:
            raise Exception(
                "Failed PUT {}, status_code {}, message {}".format(url, response.status_code, response.content)
            )
        return response

    def get(self, path, status_code, **kwargs):
        url = encode_resource_url(self._build_url(path))
        response = self._session.get(url, **kwargs)
        if response.status_code != status_code:
            raise Exception(
                "Failed GET {}, status_code {}, message {}".format(url, response.status_code, response.content)
            )
        return response

    def delete(self, path, status_code, **kwargs):
        url = encode_resource_url(self._build_url(path))
        response = self._session.delete(url, **kwargs)
        if response.status_code != status_code:
            raise Exception(
                "Failed DELETE {}, status_code {}, message {}".format(url, response.status_code, response.content)
            )
        return response


class HydroShare:

    default_host = 'www.hydroshare.org'
    default_protocol = "https"
    default_port = 443

    def __init__(
        self,
        username: str = None,
        password: str = None,
        host: str = default_host,
        protocol: str = default_protocol,
        port: int = default_port,
    ):
        self._hs_session = HydroShareSession(
            username=username, password=password, host=host, protocol=protocol, port=port
        )

    def sign_in(self) -> None:
        username = input("Username: ").strip()
        password = getpass.getpass("Password for {}: ".format(username))
        self._hs_session.set_auth((username, password))

    def search(
        self,
        creator: str = None,
        contributor: str = None,
        owner: str = None,
        group_name: str = None,
        from_date: datetime = None,
        to_date: datetime = None,
        edit_permission: bool = False,
        resource_types: List[str] = [],
        subject: List[str] = [],
        full_text_search: str = None,
        published: bool = False,
        spatial_coverage: Union[BoxCoverage, PointCoverage] = None,
    ):
        """
        Query the GET /hsapi/resource/ REST end point of the HydroShare server.
        :param creator: Filter results by the HydroShare username or email
        :param author: Filter results by the HydroShare username or email
        :param owner: Filter results by the HydroShare username or email
        :param group_name: Filter results by the HydroShare group name associated with resources
        :param from_date: Filter results to those created after from_date.  Must be datetime.date.
        :param to_date: Filter results to those created before to_date.  Must be datetime.date.  Because dates have
            no time information, you must specify date+1 day to get results for date (e.g. use 2015-05-06 to get
            resources created up to and including 2015-05-05)
        :param types: Filter results to particular HydroShare resource types. (Deprecated, resources have migrated to Composite)
        :param subject: Filter by comma separated list of subjects
        :param full_text_search: Filter by full text search
        :param edit_permission: Filter by boolean edit permission
        :param published: Filter by boolean published status
        :param spatial_coverage: Filtering by spatial coverage raises a 500, do not use.
        """

        params = {"edit_permission": edit_permission, "published": published}
        if creator:
            params["creator"] = creator
        if contributor:
            params["author"] = contributor
        if owner:
            params["owner"] = owner
        if group_name:
            params["group"] = group_name
        if resource_types:
            params["type[]"] = resource_types
        if subject:
            params["subject"] = ",".join(subject)
        if full_text_search:
            params["full_text_search"] = full_text_search
        if from_date:
            params["from_date"] = from_date.strftime('%Y-%m-%d')
        if to_date:
            params["to_date"] = to_date.strftime('%Y-%m-%d')
        if spatial_coverage:
            params["coverage_type"] = spatial_coverage.type
            if spatial_coverage.type == "point":
                params["north"] = spatial_coverage.north
                params["east"] = spatial_coverage.east
            else:
                params["north"] = spatial_coverage.northlimit
                params["east"] = spatial_coverage.eastlimit
                params["south"] = spatial_coverage.southlimit
                params["west"] = spatial_coverage.westlimit
        response = self._hs_session.get("/hsapi/resource/", 200, params=params)

        res = response.json()
        results = res['results']
        print(res['count'])
        for item in results:
            yield ResourcePreview(**item)

        while res['next']:
            next_url = res['next']
            next_url = urlparse(next_url)
            path = next_url.path
            params = next_url.query
            response = self._hs_session.get(path, 200, params=params)
            res = response.json()
            results = res['results']
            for item in results:
                yield ResourcePreview(**item)

    def resource(self, resource_id: str, validate: bool = True) -> Resource:
        res = Resource("/resource/{}/data/resourcemap.xml".format(resource_id), self._hs_session)
        if validate:
            res.metadata
        return res

    def create(self) -> Resource:
        response = self._hs_session.post('/hsapi/resource/', status_code=201)
        resource_id = response.json()['resource_id']
        return self.resource(resource_id)

    def user(self, user_id: int) -> User:
        response = self._hs_session.get(f'/hsapi/userDetails/{user_id}/', status_code=200)
        return User(**response.json())


def encode_resource_url(url):
    """
    URL encodes a full resource file/folder url.
    :param url: a string url
    :return: url encoded string
    """
    import urllib

    parsed_url = urllib.parse.urlparse(url)
    url_encoded_path = pathname2url(parsed_url.path)
    encoded_url = parsed_url._replace(path=url_encoded_path).geturl()
    return encoded_url


def is_folder(path):
    """Checks for an extension to determine if the path is to a folder"""
    return splitext(path)[1] == ''
