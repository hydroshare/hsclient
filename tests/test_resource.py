import pytest
import requests
import sys

from hs_rdf.implementations.hydroshare import Resource, HydroShareSession

@pytest.fixture()
def resource(requests_mock):

    mock_data(requests_mock, "39ec2bee16614f96a1d41b0916c72258/data/resourcemap.xml")
    mock_data(requests_mock, "39ec2bee16614f96a1d41b0916c72258/data/resourcemetadata.xml")
    return Resource("https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/resourcemap.xml",
                    HydroShareSession("user", "password"))

def mock_data(requests_mock, file_path):
    local_file_path = file_path.rstrip("#aggregation")
    with open("data/{}".format(local_file_path), "rb") as f:
        requests_mock.get("https://dev-hs-1.cuahsi.org/resource/{}".format(file_path), content=f.read())

def test_system_metadata():
    pass

def test_access_rules():
    pass

def test_references():
    pass

def test_delete():
    pass

def test_upload():
    pass

def test_delete_folder():
    pass
