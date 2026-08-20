import pytest
from hsmodels.schemas.enums import AggregationType

pytestmark = pytest.mark.integration


def _wait_for_raster_aggregation(resource, attempts=10):
    """Poll for async metadata extraction to materialize raster aggregation metadata."""
    for _ in range(attempts):
        resource.refresh()
        agg = resource.aggregation(type=AggregationType.GeographicRasterAggregation)
        if agg is not None:
            return agg
    return None


def test_raster_aggregation_discovery_and_properties_for_vrt_with_tifs(new_resource):
    root_path = "data/test_resource_metadata_files/"
    data_files = ["logan.vrt", "logan1.tif", "logan2.tif"]

    new_resource.file_upload(*[f"{root_path}{name}" for name in data_files], refresh=False)

    agg = _wait_for_raster_aggregation(new_resource)

    assert agg is not None
    assert agg._aggregation_type == AggregationType.GeographicRasterAggregation
    assert agg.metadata.type == AggregationType.GeographicRasterAggregation

    assert agg.main_file_path.endswith("logan.vrt")
    assert agg.jsonld_metadata_path.endswith("/.hsjsonld/logan.vrt.json")
    assert agg.user_metadata_path.endswith("/.hsmetadata/logan.vrt.user_metadata.json")
    assert agg.extracted_metadata_path.endswith("/.hsmetadata/logan.vrt.json")
    assert new_resource.resource_id in agg.bucket_path

    agg_file_paths = {f.path for f in agg.files()}
    assert len(agg_file_paths) == 3
    assert agg_file_paths == {"logan.vrt", "logan1.tif", "logan2.tif"}

    assert len(new_resource.files(search_aggregations=True)) == 3
    assert len(new_resource.files(search_aggregations=False)) == 0

    assert new_resource.aggregation(file__path="logan.vrt") is not None


def test_raster_aggregation_discovery_and_properties_for_single_tif(new_resource):
    root_path = "data/test_resource_metadata_files/"
    new_resource.file_upload(f"{root_path}logan1.tif", refresh=False)

    agg = _wait_for_raster_aggregation(new_resource)

    assert agg is not None
    assert agg._aggregation_type == AggregationType.GeographicRasterAggregation
    assert agg.metadata.type == AggregationType.GeographicRasterAggregation

    assert agg.main_file_path.endswith("logan1.tif")
    assert agg.jsonld_metadata_path.endswith("/.hsjsonld/logan1.tif.json")
    assert agg.user_metadata_path.endswith("/.hsmetadata/logan1.tif.user_metadata.json")
    assert agg.extracted_metadata_path.endswith("/.hsmetadata/logan1.tif.json")
    assert new_resource.resource_id in agg.bucket_path

    agg_files = agg.files()
    assert len(agg_files) == 1
    assert agg_files[0].path == "logan1.tif"

    assert len(new_resource.files(search_aggregations=True)) == 1
    assert len(new_resource.files(search_aggregations=False)) == 0

    assert new_resource.aggregation(file__path="logan1.tif") is not None
