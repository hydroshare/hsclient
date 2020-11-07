import pytest

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
    new_resource.upload("data/composite.zip")
    new_resource.refresh()
    return new_resource

def test_resource(new_resource):

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

def test_delete(hydroshare, new_resource):
    res_id = new_resource.resource_id
    new_resource.delete()
    try:
        res = hydroshare.resource(res_id)
    except Exception as e:
        assert str(e) == "failed to retrieve {}".format(res._map_url)

def test_existing(resource):
    assert len(resource.files) == 5


def test_files(resource):

    assert len(resource.files) == 9
    files = [str(f) for f in resource.files]
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/test_folder/deep/test1.txt" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/hs_restclient_demo.ipynb" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/test_folder/deep/test3.txt" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/test_folder/deep/test2.txt" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/other.txt" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/testing.xml" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/test_folder/deep/test.txt" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/test.txt" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/test.xml" in files


def test_aggregations(resource):

    assert len(resource.aggregations) == 5
    assert isinstance(resource.aggregations[0], Aggregation)

    agg_tested = False
    for agg in resource.aggregations:
        map_url = agg._map_url
        if map_url == "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/logan_resmap.xml#aggregation":
            assert len(agg.files) == 3
            assert len(agg.aggregations) == 0
            agg_tested = True
    assert agg_tested


def test_metadata(resource):

    assert isinstance(resource.metadata, ResourceMetadata)
    assert resource.metadata.title == "testing from scratch"

def test_metadata_url(resource):

    assert resource.metadata_url == \
           "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/resourcemetadata.xml"

def test_url(resource):

    assert resource.url == \
           "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258"

def test_download():
    pass

def test_delete():
    pass

def test_remove():
    pass

def test_upload():
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



def test_save(resource):
    pass
