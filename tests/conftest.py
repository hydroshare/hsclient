import os

import pytest

from hsclient import HydroShare


@pytest.fixture(scope="function")
def change_test_dir(request):
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture()
def hydroshare(change_test_dir):
    # Use environment variables with sensible defaults for local development
    # CI should set HYDRO_USERNAME, HYDRO_PASSWORD, and optionally HYDRO_HOST
    hs = HydroShare(
        username=os.getenv("HYDRO_USERNAME", "admin"),
        password=os.getenv("HYDRO_PASSWORD", "default"),
        host=os.getenv("HYDRO_HOST", "localhost"),
        port=int(os.getenv("HYDRO_PORT", "8000")),
        protocol=os.getenv("HYDRO_PROTOCOL", "http"),
        s3_endpoint_url=os.getenv("HYDRO_S3_ENDPOINT_URL", "http://localhost:9002"),
    )
    return hs


@pytest.fixture()
def new_resource(hydroshare):
    new_resource = hydroshare.create()
    yield new_resource
    try:
        new_resource.delete()
    except Exception:
        # resource already deleted
        pass


@pytest.fixture()
def resource(new_resource):
    root_path = "data/test_resource_metadata_files/"
    # Use shapefile files for GeoFeature aggregation (as file unzip that was originally used for raster aggregation doesn't work - unzip
    # doesn't fire a PutObject s3 event- so no metadata extraction).
    geofiles = [
        "watersheds.shp",
        "watersheds.cpg",
        "watersheds.dbf",
        "watersheds.prj",
        "watersheds.sbn",
        "watersheds.sbx",
        "watersheds.shx",
    ]
    new_resource.file_upload(os.path.join("data", "other.txt"), refresh=False)
    # upload shapefile components
    new_resource.file_upload(*[os.path.join(root_path, file) for file in geofiles], refresh=False)

    # Give backend extraction some time to materialize JSON-LD aggregation metadata.
    for _ in range(10):
        new_resource.refresh()
        if new_resource.aggregations():
            break

    return new_resource


@pytest.fixture()
def timeseries_resource(new_resource):
    files = [
        "ODM2_Multi_Site_One_Variable.sqlite",
        "ODM2_Multi_Site_One_Variable_resmap.xml",
        "ODM2_Multi_Site_One_Variable_meta.xml",
    ]
    root_path = "data/test_resource_metadata_files/"
    new_resource.file_upload(*[os.path.join(root_path, file) for file in files], refresh=False)
    return new_resource


@pytest.fixture()
def resource_with_netcdf_aggr(new_resource):
    files = [
        "SWE_time.nc",
        "SWE_time_header_info.txt",
        "SWE_time_resmap.xml",
        "SWE_time_meta.xml",
    ]
    root_path = "data/test_resource_metadata_files/"
    new_resource.file_upload(*[os.path.join(root_path, file) for file in files], refresh=False)
    return new_resource


@pytest.fixture()
def resource_with_geofeature_aggr(new_resource):
    files = [
        "watersheds.shp",
        "watersheds.cpg",
        "watersheds.dbf",
        "watersheds.prj",
        "watersheds.sbn",
        "watersheds.sbx",
        "watersheds.shx",
        "watersheds_resmap.xml",
        "watersheds_meta.xml",
    ]
    root_path = "data/test_resource_metadata_files/"
    new_resource.file_upload(*[os.path.join(root_path, file) for file in files], refresh=False)
    return new_resource


@pytest.fixture()
def resource_with_csv_aggr(new_resource):
    files = [
        "ecoregions.csv",
        "ecoregions_resmap.xml",
        "ecoregions_meta.xml",
    ]
    root_path = "data/test_resource_metadata_files/"
    new_resource.file_upload(*[os.path.join(root_path, file) for file in files], refresh=False)
    return new_resource


@pytest.fixture()
def resource_with_raster_aggr(resource):
    return resource
