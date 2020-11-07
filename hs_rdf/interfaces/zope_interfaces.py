from zope.interface import Interface, implementer, Attribute

class IHydroShareSession(Interface):

    def set_auth(auth):
        """Overwrites the auth on the session"""

    def retrieve(url, save_path):
        """Retrieves a file using url and saving to save_path"""

    def upload_file(url, file):
        """Uploads a file"""

    def get(url):
        """Runs GET on the url"""

    def delete(url):
        """Runs DELETE on the url"""

    def post(url):
        """Runs POST on the url"""

    def put(url):
        """Runs PUT on the url"""


class IHydroShare(Interface):

    def sign_in():
        """User/password prompts to use in a session"""

    def search():
        """Uses haystack drf"""

    def resource(resource_id):
        """Retrieve a resource metadata and files using the resource_id"""

    def create():
        """Creates a resource and returns the newly created Resource object"""


class IFile(Interface):

    url = Attribute("The url of the file")
    name = Attribute("The name of the file")
    full_path = Attribute("The full path of the file")
    relative_folder = Attribute("The relative folder holding the file")
    checksum = Attribute("Checksum of the file")

    def download(save_path):
        """Downloads the file to save_path"""

    def delete():
        """Deletes the file"""

    def overwrite(new_file):
        """Overwrites the file with new_file"""

    def rename(file_name):
        """Updates the name of the file to file_name"""

    def unzip():
        """Unzips the file if it is a zip"""

    def aggregate():
        """Creates an aggregation using the file"""

class IAggregation(Interface):

    files = Attribute("A list of files within")
    aggregations = Attribute("A list of aggregations within")
    metadata = Attribute("The metadata")
    metadata_url = Attribute("The url of the metadata")
    url = Attribute("The url of the resource")

    def as_blah(self):
        """"""

    def download(save_path):
        """Downloads a zip of the aggregation"""

    def delete():
        """Deletes the aggregation"""

    def remove(self):
        """removes the aggregation by removing the metadata associated with the files"""

    def upload(*files, dest_folder):
        """Uploads each file to the dest_folder"""

    def refresh():
        """Refreshes metadata and files"""

    def save():
        """Saves the metadata"""


class IResource(Interface):

    files = Attribute("A list of files within")
    aggregations = Attribute("A list of aggregations within")
    metadata = Attribute("The metadata")
    metadata_url = Attribute("The url of the metadata")
    url = Attribute("The url of the resource")
    resource_id = Attribute("The resource id of the resource")

    def create_reference(file_name, url):
        """"""

    def update_reference(file, url):
        """"""

    def download(save_path):
        """Downloads a zipped bagit of the resource"""

    def delete():
        """Deletes the resource"""

    def upload(*files, dest_folder, auto_aggregate):
        """Uploads each file to the dest_folder"""

    def delete_folder(folder_path):
        """Deletes each file within folder_path"""

    def system_metadata():
        """JSON of the resource metadata"""

    def access_rules(public):
        """Sets the resource to public or private, check api to see if more could be done"""

    def refresh():
        """Refreshes metadata and files"""

    def save():
        """Saves the metadata"""
