import pytest
import tempfile
import os

from hs_rdf.implementations.hydroshare import HydroShare, Aggregation
from hs_rdf.schemas import ResourceMetadata


@pytest.fixture()
def hydroshare():
    hs = HydroShare('sblack', 'password')
    return hs

@pytest.fixture()
def new_resource(hydroshare):
    new_resource = hydroshare.create()
    yield new_resource
    try:
        resource.delete()
    except:
        # resource already deleted
        pass

@pytest.fixture()
def resource(new_resource):
    new_resource.upload("data/georaster_composite.zip")
    new_resource.refresh()
    return new_resource

def test_resource_metadata_updating(new_resource):

    assert 0 == len(new_resource.metadata.subjects)

    new_resource.metadata.subjects = ['sub1', 'sub2']
    new_resource.metadata.title = "resource test"

    new_resource.save()
    new_resource.refresh()

    assert 'resource test' == new_resource.metadata.title
    assert 2 == len(new_resource.metadata.subjects)

def test_system_metadata(new_resource):

    sys_metadata = new_resource.system_metadata()
    assert 'date_created' in sys_metadata

def test_resource_delete(hydroshare, new_resource):
    res_id = new_resource.resource_id
    new_resource.delete()
    try:
        res = hydroshare.resource(res_id)
    except Exception as e:
        assert str(e) == "failed to retrieve {}".format(res._map_url)

def test_files_aggregations(resource):
    assert len(resource.files) == 1
    assert len(resource.aggregations) == 1
    assert len(resource.aggregations[0].files) == 3
    assert len(resource.aggregations[0].aggregations) == 0


def test_metadata(resource):
    assert isinstance(resource.metadata, ResourceMetadata)
    assert resource.metadata.title == "testing from scratch"
    assert resource.aggregations[0].metadata.title == "logan1"

def test_resource_download(new_resource):
    with tempfile.TemporaryDirectory() as tmp:
        bag = new_resource.download(tmp)
        assert os.path.exists(bag)
        assert bag.endswith(".zip")
    pass

def test_file_download():
    pass

def test_aggregation_download():
    pass

def test_aggregation_delete():
    pass

def test_aggregation_remove():
    pass

def test_upload():
    pass

def test_file_overwrite():
    pass

def test_file_rename():
    pass

def test_file_aggregate():
    pass

def test_create_update_reference():
    pass

def test_delete_folder():
    pass

def test_access_rules():
    pass

def test_refresh(resource):
    resource.metadata
    resource.files
    resource.aggregations

    assert None is not resource._retrieved_map
    assert None is not resource._retrieved_metadata
    assert None is not resource._parsed_files
    assert None is not resource._parsed_aggregations

    resource.refresh()

    assert None is resource._retrieved_map
    assert None is resource._retrieved_metadata
    assert None is resource._parsed_files
    assert None is resource._parsed_aggregations
