import json
import os
import requests
import re
import getpass
import zipfile
import tempfile
import time

from zipfile import ZipFile
from urllib.parse import urlparse, urlencode

from enum import Enum

from hs_rdf.schemas import load_rdf, rdf_string
from hs_rdf.schemas.fields import User
from hs_rdf.schemas.resource import ResourceMetadata, ResourceMetadataInRDF

RESOURCE_PATTERN = re.compile('(.*)/resource/([A-z0-9\-_]{32})')

def is_aggregation(path):
    return path.endswith('#aggregation')


class AggregationType(Enum):

    SingleFileAggregation = "SingleFile"
    FileSetAggregation = "FileSet"
    GeographicRasterAggregation = "GeoRaster"
    MultidimensionalAggregation = "NetCDF"
    GeographicFeatureAggregation = "GeoFeature"
    ReferencedTimeSeriesAggregation = "RefTimeseries"
    TimeSeriesAggregation = "TimeSeries"


def main_file_type(type: AggregationType):
    if type == AggregationType.GeographicRasterAggregation:
        return ".vrt"
    if type == AggregationType.MultidimensionalAggregation:
        return ".nc"
    if type == AggregationType.GeographicFeatureAggregation:
        return ".shp"
    if type == AggregationType.ReferencedTimeSeriesAggregation:
        return ".refts.json"
    if type == AggregationType.TimeSeriesAggregation:
        return ".sqlite"
    return None


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
        if not path.startswith("/"):
            path = "/" + path
        if "?" not in path and not path.endswith("/"):
            path = path + "/"
        return self.base_url + path

    def retrieve_string(self, path):
        file = self.get(path, status_code=200, allow_redirects=True)
        return file.content.decode()

    def retrieve_file(self, path, save_path=""):
        file = self.get(path, status_code=200, allow_redirects=True)

        cd = file.headers['content-disposition']
        filename = cd.split("filename=")[1].strip('"')
        downloaded_file = os.path.join(save_path, filename)
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

    def retrieve_zip(self, path, save_path=""):
        file = self.get(path, status_code=200, allow_redirects=True)

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
        url = self._build_url(path)
        if params:
            url = url + "?" + urlencode(params)
        response = self._session.post(url, data=data, **kwargs)
        if response.status_code != status_code:
            raise Exception("Failed POST {}, status_code {}, message {}".format(url, response.status_code,
                                                                                response.content))
        return response

    def put(self, path, status_code, data=None, **kwargs):
        url = self._build_url(path)
        response = self._session.put(url, data=data, **kwargs)
        if response.status_code != status_code:
            raise Exception("Failed PUT {}, status_code {}, message {}".format(url, response.status_code,
                                                                               response.content))
        return response

    def get(self, path, status_code, **kwargs):
        url = self._build_url(path)
        response = self._session.get(url, **kwargs)
        if response.status_code != status_code:
            raise Exception("Failed GET {}, status_code {}, message {}".format(url, response.status_code,
                                                                               response.content))
        return response

    def delete(self, path, status_code, **kwargs):
        url = self._build_url(path)
        response = self._session.delete(url, **kwargs)
        if response.status_code != status_code:
            raise Exception("Failed DELETE {}, status_code {}, message {}".format(url, response.status_code,
                                                                                  response.content))
        return response


class HydroShare:

    default_host = 'localhost'
    default_protocol = "http"
    default_port = 8000

    def __init__(self, username=None, password=None, host=default_host, protocol=default_protocol, port=default_port):
        self._hs_session = HydroShareSession(username=username, password=password, host=host, protocol=protocol, port=port)

    def sign_in(self):
        username = input("Username: ").strip()
        password = getpass.getpass("Password for {}: ".format(username))
        self._hs_session.set_auth((username, password))

    def search(self):
        pass

    def resource(self, resource_id, validate=True):
        return Resource("/resource/{}/data/resourcemap.xml".format(resource_id), self._hs_session)
        if validate:
            res.metadata
        return res

    def create(self):
        response = self._hs_session.post('/hsapi/resource/', status_code=201)
        resource_id = response.json()['resource_id']
        return self.resource(resource_id)

    def user(self, user_id: int):
        response = self._hs_session.get(f'/hsapi/userDetails/{user_id}/', status_code=200)
        return User(**response.json())



class File:

    def __init__(self, path, hs_session):
        self._path = path
        self._hs_session = hs_session

    @property
    def path(self):
        return str(self._path)

    @property
    def _hsapi_path(self):
        return self.path.replace(self.relative_path, "").replace("resource", "hsapi/resource")

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def relative_path(self):
        return "data/contents/" + self.path.split('/data/contents/', 1)[1]

    @property
    def relative_folder(self):
        return self.relative_path.rsplit(self.name, 1)[0]

    @property
    def checksum(self):
        pass

    def download(self, save_path=""):
        return self._hs_session.retrieve_file(self.path, save_path)

    def delete(self):
        path = self._hsapi_path + "files/" + self.relative_path.split("data/contents/", 1)[1]
        self._hs_session.delete(path, status_code=200)

    def rename(self, file_name):
        """Updates the name of the file to file_name"""
        rename_path = self._hsapi_path + "functions/move-or-rename/"
        source_path = self.relative_path
        target_path = self.relative_folder + file_name
        self._hs_session.post(rename_path, status_code=200, data={"source_path": source_path, "target_path": target_path})

    def unzip(self):
        if not self.name.endswith(".zip"):
            raise Exception("File {} is not a zip, and cannot be unzipped".format(self.name))
        unzip_path = self._hsapi_path + "functions/unzip/data/contents/{}/".format(self.name)
        self._hs_session.post(unzip_path, status_code=200, data={"overwrite": "true", "ingest_metadata": "true"})

    def aggregate(self, type: AggregationType):
        path = self._hsapi_path + "functions/set-file-type/" + self.relative_path.rsplit("data/contents/")[1] + "/" + type.value + "/"
        self._hs_session.post(path, status_code=201)

    def __str__(self):
        return str(self.path)


class Aggregation:

    def __init__(self, map_path, hs_session):
        self._map_path = map_path
        self._hs_session = hs_session
        self._retrieved_map = None
        self._retrieved_metadata = None
        self._parsed_files = None
        self._parsed_aggregations = None

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
    def _files(self):
        if not self._parsed_files:
            self._parsed_files = []
            for file in self._map.describes.files:
                if not is_aggregation(str(file.path)):
                    if not file.path == self.metadata_path:
                        if not str(file.path).endswith('/'): # checking for folders, shouldn't have to do this
                            self._parsed_files.append(File(file.path, self._hs_session))
        return self._parsed_files

    @property
    def _aggregations(self):
        if not self._parsed_aggregations:
            self._parsed_aggregations = []
            for file in self._map.describes.files:
                if is_aggregation(str(file.path)):
                    self._parsed_aggregations.append(Aggregation(file.path, self._hs_session))
        return self._parsed_aggregations

    def save(self):
        metadata_file = self.metadata_path.split("/data/contents/", 1)[1]
        metadata_string = rdf_string(self._retrieved_metadata, rdf_format="xml")
        url = self._hsapi_path + "ingest_metadata/"
        self._hs_session.upload_file(url, files={'file': (metadata_file, metadata_string)})

    @property
    def files(self):
        return self._files

    @property
    def aggregations(self):
        return self._aggregations

    @property
    def metadata(self):
        return self._metadata

    @property
    def metadata_path(self):
        return urlparse(str(self._map.describes.is_documented_by)).path

    @property
    def main_file_path(self):
        mft = main_file_type(AggregationType[self.metadata.type])
        for file in self.files:
            if str(file).endswith(mft):
                return file.relative_path

    @property
    def _hsapi_path(self):
        hsapi_path = "/hsapi" + self.metadata_path[:len("/resource/b4ce17c17c654a5c8004af73f2df87ab/")]
        return hsapi_path

    @property
    def _resource_path(self):
        resource_path = self.metadata_path[:len("/resource/b4ce17c17c654a5c8004af73f2df87ab/")]
        return resource_path

    def download(self, save_path=""):
        path = self._resource_path + self.main_file_path + "?zipped=true&aggregation=true"
        path = path.replace('resource', 'django_irods/rest_download')
        return self._hs_session.retrieve_zip(path, save_path=save_path)

    def remove(self):
        path = self._hsapi_path + "functions/remove-file-type/" + AggregationType[self.metadata.type].value + "LogicalFile" + self.main_file_path.split("data/contents")[1] + "/"
        self._hs_session.post(path, status_code=200)

    def delete(self):
        path = self._hsapi_path + "functions/delete-file-type/" + AggregationType[self.metadata.type].value + "LogicalFile" + \
               self.main_file_path.split("data/contents")[1] + "/"
        self._hs_session.delete(path, status_code=200)

    def __str__(self):
        return self._map_path

    @property
    def path(self):
        return urlparse(str(self.metadata.rdf_subject)).path

    def _retrieve_and_parse(self, path):
        file_str = self._hs_session.retrieve_string(path)
        instance = load_rdf(file_str)
        return instance

    def refresh(self):
        self._retrieved_map = None
        self._retrieved_metadata = None
        self._parsed_files = None
        self._parsed_aggregations = None

class Resource(Aggregation):

    @property
    def _hsapi_path(self):
        path = urlparse(self.metadata.identifier).path
        return '/hsapi' + path

    def save(self):
        metadata_string = rdf_string(self._retrieved_metadata, rdf_format="xml")
        path = self._hsapi_path + "/ingest_metadata/"
        self._hs_session.upload_file(path, files={'file': ('resourcemetadata.xml', metadata_string)})

    @property
    def resource_id(self):
        return self._map.identifier

    @property
    def access_permission(self):
        path = self._hsapi_path + "/access/"
        response = self._hs_session.get(path, status_code=200)
        return response.json()

    def system_metadata(self):
        hsapi_path = self._hsapi_path + '/sysmeta/'
        return self._hs_session.get(hsapi_path, status_code=200).json()

    def download(self, save_path=""):
        # TODO, can we add download links to maps?
        return self._hs_session.retrieve_bag(self._hsapi_path, save_path=save_path)

    def access_rules(self, public):
        url = self._hsapi_path + "access/"

    def create_folder(self, folder):
        path = self._hsapi_path + "/folders/" + folder + "/"
        self._hs_session.put(path, status_code=201)

    def create_reference(self, file_name, url, path=''):
        request_path = self._hsapi_path.replace(self.resource_id, "") + "data-store-add-reference/"
        self._hs_session.post(request_path, data={"res_id": self.resource_id, "curr_path": path, "ref_name": file_name,
                                                  "ref_url": url},
                              status_code=200)

    def update_reference(self, file_name, url, path=''):
        request_path = self._hsapi_path.replace(self.resource_id, "") + "data_store_edit_reference_url/"
        self._hs_session.post(request_path, data={"res_id": self.resource_id, "curr_path": path,
                                                  "url_filename": file_name, "new_ref_url": url},
                              status_code=200)

    def delete(self):
        """"""
        hsapi_path = self._hsapi_path
        self._hs_session.delete(hsapi_path, status_code=204)
        self.refresh()

    def upload(self, *files, dest_relative_path=""):
        if len(files) == 1:
            self._upload(files[0], dest_relative_path=dest_relative_path)
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                zipped_file = os.path.join(tmpdir, 'files.zip')
                with ZipFile(os.path.join(tmpdir, zipped_file), 'w') as zipped:
                    for file in files:
                        zipped.write(file, os.path.basename(file))
                self._upload(zipped_file, dest_relative_path=dest_relative_path)
                unzip_path = self._hsapi_path + "/functions/unzip/data/contents/{}/".format(os.path.join(dest_relative_path, os.path.basename(file)))
                self._hs_session.post(unzip_path)

    def _upload(self, file, dest_relative_path):
        stripped_path = dest_relative_path.strip("/")
        stripped_path = stripped_path + "/" if stripped_path else ""
        path = self._hsapi_path + "/files/" + stripped_path
        response = self._hs_session.upload_file(path, files={'file': open(file, 'rb')}, status_code=201)
        return response

    def delete_folder(self, folder_path):
        """Deletes each file within folder_path"""
