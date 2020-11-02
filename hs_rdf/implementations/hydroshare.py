import os
import requests

from zope.interface import implementer

from hs_rdf.interfaces.zope_interfaces import IHydroShareSession, IHydroShare, IFile, IAggregation, IResource
from hs_rdf.schemas import load_rdf


def is_aggregation(path):
    return path.endswith('#aggregation')


@implementer(IHydroShareSession)
class HydroShareSession:

    def __init__(self, username, password):
        self._session = requests.Session()
        if username and password:
            self.set_auth(username, password)

    def set_auth(self, auth):
        self._session.auth = auth

    def retrieve(self, url, save_path):
        file = self._session.request('GET', url, allow_redirects=True)

        with open(save_path, "wb") as f:
            f.write(file.content)


@implementer(IHydroShare)
class HydroShare:

    default_host = 'dev-hs-1.cuahsi.org'

    def __init__(self, username=None, password=None, host=default_host):
        self._hs_session = HydroShareSession(username=username, password=password)
        self.host = host

    def sign_in(self):
        import getpass
        username = input("Username: ").strip()
        password = getpass.getpass("Password for {}: ".format(username))
        self._hs_session.set_auth((username, password))

    def search(self):
        pass

    def resource(self, resource_id):
        #TODO check resource_id for validity
        return Resource("https://{}/resource/{}/data/resourcemap.xml".format(self.host, resource_id), self._hs_session)


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
    def relative_path(self):
        return self._url.path.split('/data/contents/', 1)[1]

    @property
    def relative_folder(self):
        return self.relative_path.rsplit(self.name, 1)[0]

    def download(self, save_path):
        self._hs_session.retrieve(self.url, save_path)

    def delete(self):
        pass


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
        return self._map.describes.is_documented_by

    def download(self, save_path):
        pass

    def delete(self):
        pass

    def upload(self, *files, dest_relative_path):
        pass

    def __str__(self):
        return self._map_url

    def _retrieve_and_parse(self, url):
        filename = 'retrieve_metadata.xml'
        try:
            self._hs_session.retrieve(url, filename)
            instance = load_rdf(filename, file_format='xml')
        finally:
            os.remove(filename)

        return instance

@implementer(IResource)
class Resource(Aggregation):

    def system_metadata(self):
        pass

    def access_rules(self, public):
        pass