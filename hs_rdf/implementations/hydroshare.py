import json
import os
import requests
import re
import getpass
import zipfile
import tempfile
import time

from zope.interface import implementer
from zipfile import ZipFile
from urllib.parse import urlparse, urlencode

from enum import Enum

from hs_rdf.interfaces.zope_interfaces import IHydroShareSession, IHydroShare, IFile, IAggregation, IResource
from hs_rdf.schemas import load_rdf


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


@implementer(IHydroShareSession)
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
        if not path.endswith("/"):
            path = path + "/"
        return self.base_url + path

    def retrieve_string(self, path):
        url = self._build_url(path)
        file = self._session.get(url, allow_redirects=True)
        if file.status_code != 200:
            if file.status_code == 404:
                raise Exception("Not Found - {}".format(url))
            raise Exception("Failed to retrieve {}, status_code {}, message {}".format(url,
                                                                                       file.status_code,
                                                                                       file.text))
        return file.text

    def retrieve_file(self, path, save_path=""):
        url = self._build_url(path)
        file = self._session.get(url, allow_redirects=True)

        cd = file.headers['content-disposition']
        filename = cd.split("filename=")[1].strip('"')
        downloaded_file = os.path.join(save_path, filename)
        with open(downloaded_file, 'wb') as f:
            f.write(file.content)
        return downloaded_file

    def retrieve_bag(self, path, save_path=""):
        url = self._build_url(path)
        file = self._session.get(url, allow_redirects=True)

        if file.headers['Content-Type'] != "application/zip":
            time.sleep(1)
            return self.retrieve_bag(path, save_path)
        return self.retrieve_file(path, save_path)

    def check_task(self, task_id):
        url = self._build_url("/hsapi/taskstatus/")
        response = self._session.get(url + task_id + "/")
        return response.json()['status']

    def retrieve_zip(self, path, save_path=""):
        url = self._build_url(path)
        file = self._session.get(url, allow_redirects=True)

        json_response = file.json()
        task_id = json_response['task_id']
        download_path = json_response['download_path']
        zip_status = json_response['zip_status']
        if zip_status == "Not ready":
            while self.check_task(task_id) != 'true':
                time.sleep(1)
        return self.retrieve_file(download_path, save_path)

    def upload_file(self, path, files):
        url = self._build_url(path)
        return self._session.post(url, files=files)

    def post(self, path, data=None, params={}):
        url = self._build_url(path)
        if params:
            url = url + "?" + urlencode(params)
        return self._session.post(url, data=data)

    def put(self, path, data=None):
        url = self._build_url(path)
        return self._session.put(url, data=data)

    def get(self, path):
        url = self._build_url(path)
        return self._session.get(url)

    def delete(self, path):
        url = self._build_url(path)
        return self._session.delete(url)


@implementer(IHydroShare)
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
        response = self._hs_session.post('/hsapi/resource/')
        resource_id = response.json()['resource_id']
        return self.resource(resource_id)


@implementer(IFile)
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
        response = self._hs_session.delete(path)
        response.status_code

    def rename(self, file_name):
        """Updates the name of the file to file_name"""
        rename_path = self._hsapi_path + "functions/move-or-rename/"
        source_path = self.relative_path
        target_path = self.relative_folder + file_name
        response = self._hs_session.post(rename_path, data={"source_path": source_path, "target_path": target_path})
        response.status_code

    def unzip(self):
        if not self.name.endswith(".zip"):
            raise Exception("File {} is not a zip, and cannot be unzipped".format(self.name))
        unzip_path = self._hsapi_path + "functions/unzip/data/contents/{}/".format(self.name)
        response = self._hs_session.post(unzip_path, {"overwrite": "true", "ingest_metadata": "true"})
        response.status_code

    def aggregate(self, type: AggregationType):
        path = self._hsapi_path + "functions/set-file-type/" + self.relative_path.rsplit("data/contents/")[1] + "/" + type.value + "/"
        response = self._hs_session.post(path)
        response.status_code

    def __str__(self):
        return str(self.path)


@implementer(IAggregation)
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
    def type(self):
        return self.metadata.rdf_type.split("/terms/")[1]

    @property
    def main_file_path(self):
        mft = main_file_type(AggregationType[self.type])
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

    def download(self, save_path):
        path = self._resource_path + self.main_file_path + "?zipped=true&aggregation=true"
        path = path.replace('resource', 'django_irods/rest_download')
        return self._hs_session.retrieve_zip(path, save_path=save_path)

    def remove(self):
        path = self._hsapi_path + "functions/remove-file-type/" + AggregationType[self.type].value + "LogicalFile" + self.main_file_path.split("data/contents")[1] + "/"
        response = self._hs_session.post(path)
        response.status_code
        pass

    def delete(self):
        path = self._hsapi_path + "functions/delete-file-type/" + AggregationType[self.type].value + "LogicalFile" + \
               self.main_file_path.split("data/contents")[1] + "/"
        response = self._hs_session.delete(path)
        response.status_code
        pass

    def __str__(self):
        return self._map_path

    @property
    def path(self):
        return urlparse(str(self.metadata.rdf_subject)).path

    def _retrieve_and_parse(self, path):
        file_str = self._hs_session.retrieve_string(path)
        instance = load_rdf(file_str, file_format='xml')
        return instance

    def refresh(self):
        self._retrieved_map = None
        self._retrieved_metadata = None
        self._parsed_files = None
        self._parsed_aggregations = None

@implementer(IResource)
class Resource(Aggregation):

    @property
    def _hsapi_path(self):
        path = urlparse(self.metadata.identifier.hydroshare_identifier).path
        return '/hsapi' + path

    def save(self):
        self._hs_session.upload_file(self._hsapi_path + '/ingest_metadata/',
                                     files={'file': ('resourcemetadata.xml', self.metadata.rdf_string(rdf_format="xml"))})

    @property
    def resource_id(self):
        return self._map.identifier

    @property
    def access_permission(self):
        path = self._hsapi_path + "/access/"
        response = self._hs_session.get(path)
        return response.json()

    def system_metadata(self):
        hsapi_path = self._hsapi_path + '/sysmeta/'
        return self._hs_session.get(hsapi_path).json()

    def download(self, save_path):
        # TODO, can we add download links to maps?
        return self._hs_session.retrieve_bag(self._hsapi_path, save_path=save_path)

    def access_rules(self, public):
        url = self._hsapi_path + "access/"

    def create_folder(self, folder):
        path = self._hsapi_path + "/folders/" + folder + "/"
        response = self._hs_session.put(path)
        response.status_code

    def create_reference(self, file_name, url, path=''):
        request_path = self._hsapi_path.replace(self.resource_id, "") + "data-store-add-reference/"
        response = self._hs_session.post(request_path, data={"res_id": self.resource_id,
                                                             "curr_path": path,
                                                             "ref_name": file_name,
                                                             "ref_url": url})
        response.status_code

    def update_reference(self, file_name, url, path=''):
        request_path = self._hsapi_path.replace(self.resource_id, "") + "data_store_edit_reference_url/"
        response = self._hs_session.post(request_path, data={"res_id": self.resource_id,
                                                             "curr_path": path,
                                                             "url_filename": file_name,
                                                             "new_ref_url": url})
        response.status_code

    def delete(self):
        """"""
        hsapi_path = self._hsapi_path
        response = self._hs_session.delete(hsapi_path)
        if response.status_code != 204:
            raise Exception("Failed to delete - status code {} - path {}".format(response.status_code, hsapi_path))
        self.refresh()

    def upload(self, *files, dest_relative_path=""):
        if len(files) == 1:
            response = self._upload(files[0], dest_relative_path=dest_relative_path)
            response.status_code
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                zipped_file = os.path.join(tmpdir, 'files.zip')
                with ZipFile(os.path.join(tmpdir, zipped_file), 'w') as zipped:
                    for file in files:
                        zipped.write(file, os.path.basename(file))
                self._upload(zipped_file, dest_relative_path=dest_relative_path)
                unzip_path = self._hsapi_path + "/functions/unzip/data/contents/{}/".format(os.path.join(dest_relative_path, os.path.basename(file)))
                response = self._hs_session.post(unzip_path)
                response.status_code

    def _upload(self, file, dest_relative_path):
        stripped_path = dest_relative_path.strip("/")
        stripped_path = stripped_path + "/" if stripped_path else ""
        path = self._hsapi_path + "/files/" + stripped_path
        response = self._hs_session.upload_file(path, files={'file': open(file, 'rb')})
        return response

    def delete_folder(self, folder_path):
        """Deletes each file within folder_path"""
