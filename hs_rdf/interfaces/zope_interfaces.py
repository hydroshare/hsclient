from zope.interface import Interface, implementer, Attribute

class IHydroShareSession(Interface):

    def retrieve(url, save_path):
        """Retrieves a file using url and saving to save_path"""

    def set_auth(auth):
        """Overwrites the auth on the session"""

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
    relative_path = Attribute("The relative path of the file")
    size = Attribute("Size of the file")

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


class IAggregation(Interface):

    files = Attribute("A list of files within")
    aggregations = Attribute("A list of aggregations within")
    metadata = Attribute("The metadata")
    metadata_url = Attribute("The url of the metadata")

    def download(save_path):
        """Downloads a zip of the aggregation"""

    def delete():
        """Deletes the aggregation"""

    def upload(*files, dest_folder):
        """Uploads each file to the dest_folder"""

    def delete_folder(folder_path):
        """Deletes each file within folder_path"""

    def refresh():
        """Refreshes metadata and files"""


class IResource(Interface):

    files = Attribute("A list of files within")
    aggregations = Attribute("A list of aggregations within")
    metadata = Attribute("The metadata")
    metadata_url = Attribute("The url of the metadata")

    def download(save_path):
        """Downloads a zipped bagit of the resource"""

    def delete():
        """Deletes the resource"""

    def upload(*files, dest_folder):
        """Uploads each file to the dest_folder"""

    def delete_folder(folder_path):
        """Deletes each file within folder_path"""

    def system_metadata():
        """JSON of the resource metadata"""

    def access_rules(public):
        """Sets the resource to public or private"""

    def refresh():
        """Refreshes metadata and files"""
