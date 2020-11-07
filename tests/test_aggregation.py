import pytest
import requests
import sys

from hs_rdf.implementations.hydroshare import Aggregation, HydroShareSession
from hs_rdf.schemas import ResourceMetadata


@pytest.fixture()
def aggregation(requests_mock):

    mock_data(requests_mock, "39ec2bee16614f96a1d41b0916c72258/data/resourcemap.xml")
    mock_data(requests_mock, "39ec2bee16614f96a1d41b0916c72258/data/resourcemetadata.xml")
    return Aggregation("https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/resourcemap.xml",
                    HydroShareSession("user", "password"))

def mock_data(requests_mock, file_path):
    local_file_path = file_path.rstrip("#aggregation")
    with open("data/{}".format(local_file_path), "rb") as f:
        requests_mock.get("https://dev-hs-1.cuahsi.org/resource/{}".format(file_path), content=f.read())

def test_files(aggregation):

    assert len(aggregation.files) == 9
    files = [str(f) for f in aggregation.files]
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/test_folder/deep/test1.txt" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/hs_restclient_demo.ipynb" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/test_folder/deep/test3.txt" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/test_folder/deep/test2.txt" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/other.txt" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/testing.xml" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/test_folder/deep/test.txt" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/test.txt" in files
    assert "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/test.xml" in files


def test_aggregations(requests_mock, aggregation):

    assert len(aggregation.aggregations) == 5
    assert isinstance(aggregation.aggregations[0], Aggregation)

    agg_tested = False
    for agg in aggregation.aggregations:
        map_url = agg._map_url
        if map_url == "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/contents/logan_resmap.xml#aggregation":
            mock_data(requests_mock, "39ec2bee16614f96a1d41b0916c72258/data/contents/logan_meta.xml")
            mock_data(requests_mock, "39ec2bee16614f96a1d41b0916c72258/data/contents/logan_resmap.xml#aggregation")
            assert len(agg.files) == 3
            assert len(agg.aggregations) == 0
            agg_tested = True
    assert agg_tested


def test_metadata(aggregation):

    assert isinstance(aggregation.metadata, ResourceMetadata)
    assert aggregation.metadata.title == "testing from scratch"

def test_metadata_url(aggregation):

    assert aggregation.metadata_url == \
           "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/resourcemetadata.xml"

def test_url(aggregation):

    assert aggregation.url == \
           "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258"

def test_download():
    pass

def test_delete():
    pass

def test_remove():
    pass

def test_upload():
    pass

def test_refresh(aggregation):
    aggregation.metadata
    aggregation.files
    aggregation.aggregations

    assert None is not aggregation._retrieved_map
    assert None is not aggregation._retrieved_metadata
    assert None is not aggregation._parsed_files
    assert None is not aggregation._parsed_aggregations

    aggregation.refresh()

    assert None is aggregation._retrieved_map
    assert None is aggregation._retrieved_metadata
    assert None is aggregation._parsed_files
    assert None is aggregation._parsed_aggregations



def test_save(aggregation):
    pass
