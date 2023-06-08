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
    hs = HydroShare(os.getenv("HYDRO_USERNAME"), os.getenv("HYDRO_PASSWORD"), host="beta.hydroshare.org")
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
    new_resource.file_upload("data/georaster_composite.zip", refresh=False)
    new_resource.file_unzip("georaster_composite.zip", refresh=False)
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
def resource_with_raster_aggr(resource):
    return resource
