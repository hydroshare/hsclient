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

from hs_rdf.interfaces.zope_interfaces import IHydroShareSession, IHydroShare, IFile, IAggregation, IResource
from hs_rdf.schemas import load_rdf


RESOURCE_PATTERN = re.compile('(.*)/resource/([A-z0-9\-_]{32})')

def is_aggregation(path):
    return path.endswith('#aggregation')


@implementer(IHydroShareSession)
class HydroShareSession:

    def __init__(self, username, password):
        self._session = requests.Session()
        if username and password:
            self.set_auth((username, password))

    def set_auth(self, auth):
        self._session.auth = auth

    def retrieve_string(self, url):
        file = self._session.get(url, allow_redirects=True)
        if file.status_code != 200:
            if file.status_code == 404:
                raise Exception("Not Found - {}".format(url))
            raise Exception("Failed to retrieve {}, status_code {}, message {}".format(url,
                                                                                       file.status_code,
                                                                                       file.text))
        return file.text

    def retrieve_task(self, url, save_path=""):
        file = self._session.get(url, allow_redirects=True)

        if file.headers['Content-Type'] != "application/zip":
            response_json = json.loads(file.text)
            if response_json["name"] == "bag download":
                if response_json["status"] == "progress":
                    time.sleep(1)
                    return self.retrieve_task(url, save_path)
                if response_json["status"] == "completed":
                    return self.retrieve_task(url, save_path)

        cd = file.headers['content-disposition']
        filename = cd.split("filename=")[1].strip('"')
        downloaded_file = os.path.join(save_path, filename)
        with open(downloaded_file, 'wb') as f:
            f.write(file.content)
        return downloaded_file

    def upload_file(self, url, files):
        return self._session.post(url, files=files)

    def post(self, url):
        return self._session.post(url)

    def get(self, url):
        return self._session.get(url)

    def delete(self, url):
        return self._session.delete(url)


@implementer(IHydroShare)
class HydroShare:

    default_host = 'dev-hs-1.cuahsi.org'

    def __init__(self, username=None, password=None, host=default_host):
        self._hs_session = HydroShareSession(username=username, password=password)
        self.host = host

    def sign_in(self):
        username = input("Username: ").strip()
        password = getpass.getpass("Password for {}: ".format(username))
        self._hs_session.set_auth((username, password))

    def search(self):
        pass

    def resource(self, resource_id, validate=True):
        return Resource("https://{}/resource/{}/data/resourcemap.xml".format(self.host, resource_id), self._hs_session)
        if validate:
            res.metadata
        return res

    def create(self):
        response = self._hs_session.post('https://{}/hsapi/resource/'.format(self.host))
        resource_id = response.json()['resource_id']
        return self.resource(resource_id)


@implementer(IFile)
class File:

    def __init__(self, file_url, hs_session):
        self._url = file_url
        self._hs_session = hs_session

    @property
    def url(self):
        return str(self._url)

    @property
    def name(self):
        return os.path.basename(self._url.path)

    @property
    def full_path(self):
        return self._url.path

    @property
    def relative_folder(self):
        return self.relative_path.rsplit(self.name, 1)[0]

    @property
    def checksum(self):
        pass

    def download(self, save_path):
        self._hs_session.retrieve(self.url, save_path)

    def delete(self):
        pass

    def overwrite(self, new_file):
        """Overwrites the file with new_file"""

    def rename(self, file_name):
        """Updates the name of the file to file_name"""

    def unzip(self):
        """Unzips the file if it is a zip"""

    def __str__(self):
        return str(self.url)


@implementer(IAggregation)
class Aggregation:

    def __init__(self, map_url, hs_session):
        self._map_url = map_url
        self._hs_session = hs_session
        self._retrieved_map = None
        self._retrieved_metadata = None
        self._parsed_files = None
        self._parsed_aggregations = None

    @property
    def _map(self):
        if not self._retrieved_map:
            self._retrieved_map = self._retrieve_and_parse(self._map_url)
        return self._retrieved_map

    @property
    def _metadata(self):
        if not self._retrieved_metadata:
            self._retrieved_metadata = self._retrieve_and_parse(self.metadata_url)
        return self._retrieved_metadata

    @property
    def _files(self):
        if not self._parsed_files:
            self._parsed_files = []
            for file_url in self._map.describes.files:
                if not is_aggregation(str(file_url.path)):
                    if not file_url == self.metadata_url:
                        if not str(file_url.path).endswith('/'): # checking for folders, shouldn't have to do this
                            self._parsed_files.append(File(file_url, self._hs_session))
        return self._parsed_files

    @property
    def _aggregations(self):
        if not self._parsed_aggregations:
            self._parsed_aggregations = []
            for file_url in self._map.describes.files:
                if is_aggregation(str(file_url.path)):
                    self._parsed_aggregations.append(Aggregation(str(file_url), self._hs_session))
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
    def metadata_url(self):
        return str(self._map.describes.is_documented_by)

    def download(self, save_path):
        pass

    def delete(self):
        pass

    def __str__(self):
        return self._map_url

    @property
    def url(self):
        return str(self.metadata.rdf_subject)

    def _retrieve_and_parse(self, url):
        file_str = self._hs_session.retrieve_string(url)
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
    def _hsapi_url(self):
        id = self.metadata.identifier.hydroshare_identifier
        id = id.replace('http://', 'https://')
        index = id.find('dev-hs-1.cuahsi.org/') + 20
        return id[:index] + 'hsapi/' + id[index:]

    def save(self):
        hsapi_url = self._hsapi_url + '/files/'
        # this is ridiculous
        self._hs_session.upload_file(hsapi_url,
                                     files={'file': ('resourcemetadata.xml', self.metadata.rdf_string(rdf_format="xml"))})

    @property
    def resource_id(self):
        return self._map.identifier

    def system_metadata(self):
        hsapi_url = self._hsapi_url + '/sysmeta/'
        return self._hs_session.get(hsapi_url).json()

    def download(self, save_path):
        # TODO, can we add download links to maps?
        return self._hs_session.retrieve_task(self._hsapi_url, save_path=save_path)

    def access_rules(self, public):
        pass

    def create_reference(self, file_name, url):
        """"""

    def update_reference(self, file, url):
        """"""

    def delete(self):
        """"""
        hsapi_url = self._hsapi_url
        response = self._hs_session.delete(hsapi_url)
        if response.status_code != 204:
            raise Exception("Failed to delete - status code {} - url {}".format(response.status_code, hsapi_url))
        self.refresh()

    def upload(self, *files, dest_relative_path=""):
        if len(files) and zipfile.is_zipfile(files[0]):
            self._upload(files[0], dest_relative_path=dest_relative_path)
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                zipped_file = os.path.join(tmpdir, 'files.zip')
                with ZipFile(os.path.join(tmpdir, zipped_file), 'w') as zipped:
                    for file in files:
                        zipped.write(file, os.path.basename(file))
                self._upload(zipped_file, dest_relative_path=dest_relative_path)

    def _upload(self, file, dest_relative_path):
        url = self._hsapi_url + "/files/" + dest_relative_path.strip("/")
        self._hs_session.upload_file(url,
                                     files={
                                         'file': open(file, 'rb')})
        unzip_url = self._hsapi_url + "/functions/unzip/data/contents/" + dest_relative_path + "{}/".format(os.path.basename(file))
        response = self._hs_session.post(unzip_url)

    def delete_folder(self, folder_path):
        """Deletes each file within folder_path"""
