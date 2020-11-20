import pytest
import tempfile
import os

from hs_rdf.implementations.hydroshare import HydroShare, AggregationType
from hs_rdf.schemas import ResourceMetadataInRDF
from hs_rdf.schemas.fields import ExtendedMetadataInRDF


@pytest.fixture()
def hydroshare():
    hs = HydroShare('admin', 'default')
    return hs

@pytest.fixture()
def new_resource(hydroshare):
    new_resource = hydroshare.create()
    yield new_resource
    try:
        new_resource.delete()
    except:
        # resource already deleted
        pass

@pytest.fixture()
def resource(new_resource):
    new_resource.upload("data/georaster_composite.zip")
    new_resource.refresh()
    new_resource.files[0].unzip()
    new_resource.refresh()
    return new_resource

def test_resource_metadata_updating(new_resource):

    assert len(new_resource.metadata.subjects) == 0

    new_resource.metadata.subjects = ['sub1', 'sub2']
    new_resource.metadata.title = "resource test"
    em = [ExtendedMetadataInRDF(key="key1", value="value1"), ExtendedMetadataInRDF(key="key2", value="value2"),
          ExtendedMetadataInRDF(key="key3", value="value3")]
    new_resource.metadata.extended_metadatas = em

    new_resource.save()
    new_resource.refresh()

    assert 'resource test' == new_resource.metadata.title
    assert len(new_resource.metadata.subjects) == 2

    assert len(new_resource.metadata.extended_metadatas) == 3
    keys = ['key1', 'key2', 'key3']
    values = ['value1', 'value2', 'value3']
    for i, em in enumerate(new_resource.metadata.extended_metadatas):
        assert em.key in keys
        keys.remove(em.key)
        assert em.value in values
        values.remove(em.value)

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
    assert isinstance(resource.metadata, ResourceMetadataInRDF)
    assert resource.metadata.title == "testing from scratch"
    assert resource.aggregations[0].metadata.title == "logan1"

def test_resource_download(new_resource):
    with tempfile.TemporaryDirectory() as tmp:
        bag = new_resource.download(tmp)
        assert os.path.exists(bag)
        assert bag.endswith(".zip")

def test_file_download(resource):
    with tempfile.TemporaryDirectory() as tmp:
        file = resource.files[0]
        downloaded_file = file.download(tmp)
        assert os.path.exists(downloaded_file)
        assert os.path.basename(downloaded_file) == file.name

def test_aggregation_download(resource):
    assert len(resource.aggregations) == 1
    agg = resource.aggregations[0]
    with tempfile.TemporaryDirectory() as tmp:
        agg.download(tmp)
        files = os.listdir(tmp)
        assert len(files) == 1
        assert files[0] == "logan.vrt.zip"

def test_aggregation_delete(resource):
    assert len(resource.aggregations) == 1
    assert len(resource.files) == 1
    agg = resource.aggregations[0]
    agg.delete()
    resource.refresh()
    assert len(resource.aggregations) == 0
    assert len(resource.files) == 1

def test_aggregation_remove(resource):
    assert len(resource.aggregations) == 1
    assert len(resource.files) == 1
    agg = resource.aggregations[0]
    agg.remove()
    resource.refresh()
    assert len(resource.aggregations) == 0
    assert len(resource.files) == 4

def test_file_upload_and_rename(new_resource):
    assert len(new_resource.files) == 0
    new_resource.upload("data/other.txt")
    new_resource.refresh()
    assert len(new_resource.files) == 1
    file = new_resource.files[0]
    file.rename("updated.txt")
    new_resource.refresh()
    assert new_resource.files[0].name == "updated.txt"

def test_file_aggregate(new_resource):
    assert len(new_resource.files) == 0
    new_resource.create_folder("folder")
    new_resource.upload("data/other.txt", dest_relative_path="folder")
    new_resource.refresh()
    assert len(new_resource.files) == 1
    new_resource.files[0].aggregate(AggregationType.SingleFileAggregation)
    new_resource.refresh()
    assert len(new_resource.files) == 0
    assert len(new_resource.aggregations) == 1
    assert len(new_resource.aggregations[0].files) == 1

def test_create_update_reference(new_resource):
    assert len(new_resource.aggregations) == 0
    new_resource.create_reference("reference", "http://studio.bakajo.com")
    new_resource.refresh()
    assert len(new_resource.aggregations) == 1
    aggregation = new_resource.aggregations[0]
    assert len(aggregation.files) == 1
    file = aggregation.files[0]
    assert file.name == "reference.url"
    with tempfile.TemporaryDirectory() as tmp:
        file.download(tmp)
        with open(os.path.join(tmp, file.name), "r") as f:
            assert "http://studio.bakajo.com" in str(f.read())

    new_resource.update_reference(new_resource.aggregations[0].files[0].name, "https://duckduckgo.com")

    with tempfile.TemporaryDirectory() as tmp:
        new_resource.aggregations[0].files[0].download(tmp)
        with open(os.path.join(tmp, file.name), "r") as f:
            assert "https://duckduckgo.com" in str(f.read())

def test_file_unzip(new_resource):
    new_resource.upload("data/georaster_composite.zip")
    new_resource.refresh()
    assert len(new_resource.files) == 1
    assert len(new_resource.aggregations) == 0
    new_resource.files[0].unzip()
    new_resource.refresh()
    assert len(new_resource.aggregations) == 1

def test_delete_file(new_resource):
    new_resource.upload("data/other.txt")
    new_resource.refresh()
    assert len(new_resource.files) == 1
    new_resource.files[0].delete()
    new_resource.refresh()
    assert len(new_resource.files) == 0

def test_delete_folder():
    pass

def test_access_rules(new_resource):
    ap = new_resource.access_permission
    pass

def test_refresh(resource):
    resource.metadata
    resource.files
    resource.aggregations

    assert resource._retrieved_map is not None
    assert resource._retrieved_metadata is not None
    assert resource._parsed_files is not None
    assert resource._parsed_aggregations is not None

    resource.refresh()

    assert resource._retrieved_map is None
    assert resource._retrieved_metadata is None
    assert resource._parsed_files is None
    assert resource._parsed_aggregations is None
