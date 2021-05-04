import os
import tempfile

import pytest
from hsmodels.schemas.enums import AggregationType, RelationType
from hsmodels.schemas.fields import Contributor, Creator, Relation

from hsclient import HydroShare


@pytest.fixture(scope="function")
def change_test_dir(request):
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture()
def hydroshare(change_test_dir):
    hs = HydroShare(os.getenv("HYDRO_USERNAME"), os.getenv("HYDRO_PASSWORD"))
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


def test_absolute_path_multiple_file_upload(new_resource):
    files = [
        "other.txt",
        "another.txt",
    ]
    root_path = "data"
    new_resource.file_upload(*[os.path.abspath(os.path.join(root_path, file)) for file in files])
    assert len(new_resource.files()) == 2


def test_absolute_path_single_file_upload(new_resource):
    rel_path = os.path.join("data", "other.txt")
    new_resource.file_upload(os.path.abspath(rel_path))
    assert len(new_resource.files()) == 1


def test_filtering_aggregations(timeseries_resource):
    timeseries_resource.refresh()
    assert len(timeseries_resource.aggregations(type=AggregationType.TimeSeriesAggregation)) == 1
    timeseries = timeseries_resource.aggregation(type=AggregationType.TimeSeriesAggregation)
    assert timeseries.metadata.type == AggregationType.TimeSeriesAggregation
    timeseries.metadata.subjects = ['a', 'b', 'c']
    timeseries.metadata.additional_metadata = {"a": "a_val", "b": "b_val"}
    timeseries.metadata.period_coverage.name = "period_coverage name"
    assert len(timeseries_resource.aggregations(additional_metadata__key="a")) == 1
    assert timeseries_resource.aggregation(additional_metadata__key="a").metadata.additional_metadata["a"] == "a_val"
    assert len(timeseries_resource.aggregations(additional_metadata__key="bad")) == 0
    assert not timeseries_resource.aggregation(additional_metadata__key="bad")
    assert len(timeseries_resource.aggregations(additional_metadata__value="a_val")) == 1
    assert timeseries_resource.aggregation(additional_metadata__key="a").metadata.additional_metadata["a"] == "a_val"
    assert len(timeseries_resource.aggregations(additional_metadata__value="bad")) == 0
    assert not timeseries_resource.aggregation(additional_metadata__value="bad")

    assert len(timeseries_resource.aggregations(subjects__contains="a")) == 1
    assert len(timeseries_resource.aggregations(subjects__contains="bad")) == 0
    assert not timeseries_resource.aggregation(subjects__contains="bad")
    assert "a" in timeseries_resource.aggregation(subjects__contains="a").metadata.subjects

    assert len(timeseries_resource.aggregations(title="changed from the Little Bear River, UT")) == 1
    assert len(timeseries_resource.aggregations(title="bad")) == 0
    assert not timeseries_resource.aggregation(title="bad")
    assert (
        timeseries_resource.aggregation(title="changed from the Little Bear River, UT").metadata.title
        == "changed from the Little Bear River, UT"
    )

    assert (
        len(
            timeseries_resource.aggregations(
                period_coverage__name="period_coverage name", title="changed from the Little Bear River, UT"
            )
        )
        == 1
    )
    assert (
        timeseries_resource.aggregation(
            period_coverage__name="period_coverage name", title="changed from the Little Bear River, UT"
        ).metadata.period_coverage.name
        == "period_coverage name"
    )

    assert len(timeseries_resource.aggregations(period_coverage__name="period_coverage name", title="bad")) == 0

    assert not timeseries_resource.aggregation(period_coverage__name="bad")
    assert len(timeseries_resource.aggregations(period_coverage__name="bad")) == 0

    assert len(timeseries_resource.aggregations(bad="does not matter")) == 0
    assert not timeseries_resource.aggregation(bad="does not matter")


def test_filtering_aggregations_by_files(timeseries_resource):
    timeseries_resource.refresh()
    assert len(timeseries_resource.aggregations(file__path="ODM2_Multi_Site_One_Variable.sqlite")) == 1
    assert timeseries_resource.aggregation(file__path="ODM2_Multi_Site_One_Variable.sqlite")
    assert len(timeseries_resource.aggregations(files__path="ODM2_Multi_Site_One_Variable.sqlite")) == 1
    assert timeseries_resource.aggregation(files__path="ODM2_Multi_Site_One_Variable.sqlite")

    assert len(timeseries_resource.aggregations(file__path="No_match.sqlite")) == 0
    assert not timeseries_resource.aggregation(file__path="No_match.sqlite")
    assert len(timeseries_resource.aggregations(files__path="No_match.sqlite")) == 0
    assert not timeseries_resource.aggregation(files__path="No_match.sqlite")


def test_filtering_files(resource):
    resource.folder_create("asdf", refresh=False)
    resource.file_upload("data/test_resource_metadata_files/asdf/testing.xml", destination_path="asdf", refresh=False)
    resource.folder_create("referenced_time_series", refresh=False)
    resource.file_upload(
        "data/test_resource_metadata_files/msf_version.refts.json", destination_path="referenced_time_series"
    )

    assert len(resource.files(search_aggregations=True)) == 6
    assert len(resource.files()) == 2
    assert resource.file()
    assert len(resource.files(folder="asdf")) == 1
    assert resource.file(folder="asdf")
    assert not resource.file(folder="bad")
    assert len(resource.files(folder="bad")) == 0

    assert len(resource.files(extension=".xml")) == 1
    assert resource.file(extension=".txt")
    assert resource.file(search_aggregations=True, extension=".json")
    assert not resource.file(extension=".json")
    assert len(resource.files(extension=".json")) == 0
    assert len(resource.files(search_aggregations=True, extension=".json")) == 1

    assert len(resource.files(path="asdf/testing.xml")) == 1
    assert resource.file(path="asdf/testing.xml")
    assert len(resource.files(name="testing.xml")) == 1
    assert resource.file(name="testing.xml")

    assert len(resource.files(bad="testing.xml")) == 0
    assert not resource.file(bad="testing.xml")


def test_creator_order(new_resource):
    res = new_resource  # hydroshare.resource("1248abc1afc6454199e65c8f642b99a0")
    res.metadata.creators.append(Creator(name="Testing"))
    res.save()
    assert res.metadata.creators[1].name == "Testing"
    reversed = [res.metadata.creators[1], res.metadata.creators[0]]
    res.metadata.creators = reversed
    res.save()
    assert res.metadata.creators[0].name == "Testing"


def test_resource_metadata_updating(new_resource):

    assert len(new_resource.metadata.subjects) == 0

    new_resource.metadata.subjects = ['sub1', 'sub2']
    new_resource.metadata.title = "resource test"
    new_resource.metadata.additional_metadata = {"key1": "value1", "key2": "value2", "key3": "value3"}
    new_resource.metadata.abstract = "world’s"
    new_resource.metadata.relations = [Relation(type=RelationType.isCopiedFrom, value="is hosted by value")]

    new_resource.save()

    assert 'resource test' == new_resource.metadata.title
    assert len(new_resource.metadata.subjects) == 2

    assert len(new_resource.metadata.additional_metadata) == 3
    assert new_resource.metadata.additional_metadata["key1"] == "value1"
    assert new_resource.metadata.additional_metadata["key2"] == "value2"
    assert new_resource.metadata.additional_metadata["key3"] == "value3"
    assert new_resource.metadata.abstract == "world’s"

    assert new_resource.metadata.relations == [Relation(type=RelationType.isCopiedFrom, value="is hosted by value")]


def test_system_metadata(new_resource):

    sys_metadata = new_resource.system_metadata()
    assert 'date_created' in sys_metadata


def test_resource_delete(hydroshare, new_resource):
    res_id = new_resource.resource_id
    new_resource.delete()
    try:
        res = hydroshare.resource(res_id)
        assert False
    except Exception as e:
        assert f"No resource was found for resource id:{res_id}" in str(e)


def test_files_aggregations(resource):
    resource.refresh()
    assert len(resource.files()) == 1
    assert len(resource.aggregations()) == 1
    assert len(resource.aggregations()[0].files()) == 3
    assert len(resource.aggregations()[0].aggregations()) == 0


def test_resource_download(new_resource):
    with tempfile.TemporaryDirectory() as tmp:
        bag = new_resource.download(save_path=tmp)
        assert os.path.exists(bag)
        assert bag.endswith(".zip")


def test_file_download(resource):
    resource.refresh()
    with tempfile.TemporaryDirectory() as tmp:
        file = resource.files()[0]
        downloaded_file = resource.file_download(file, save_path=tmp)
        assert os.path.exists(downloaded_file)
        assert os.path.basename(downloaded_file) == file.name


def test_aggregation_download(resource):
    resource.refresh()
    assert len(resource.aggregations()) == 1
    agg = resource.aggregations()[0]
    with tempfile.TemporaryDirectory() as tmp:
        resource.aggregation_download(agg, tmp)
        files = os.listdir(tmp)
        assert len(files) == 1
        assert files[0] == "logan.vrt.zip"


def test_aggregation_delete(resource):
    resource.refresh()
    assert len(resource.aggregations()) == 1
    assert len(resource.files()) == 1
    agg = resource.aggregations()[0]
    resource.aggregation_delete(agg)
    assert len(resource.aggregations()) == 0
    assert len(resource.files()) == 1


def test_aggregation_remove(resource):
    resource.refresh()
    assert len(resource.aggregations()) == 1
    assert len(resource.files()) == 1
    agg = resource.aggregations()[0]
    resource.aggregation_remove(agg)
    assert len(resource.aggregations()) == 0
    assert len(resource.files()) == 4


def test_file_upload_and_rename(new_resource):
    assert len(new_resource.files()) == 0
    new_resource.file_upload("data/other.txt", refresh=False)
    new_resource.file_rename("other.txt", "updated.txt")
    assert len(new_resource.files()) == 1
    assert new_resource.files()[0].name == "updated.txt"


def test_file_aggregate(new_resource):
    assert len(new_resource.files()) == 0
    new_resource.folder_create("folder", refresh=False)
    new_resource.file_upload("data/other.txt", destination_path="folder", refresh=False)
    new_resource.file_aggregate("folder/other.txt", agg_type=AggregationType.SingleFileAggregation)
    assert len(new_resource.files()) == 0
    assert len(new_resource.aggregations()) == 1
    assert len(new_resource.aggregations()[0].files()) == 1


def test_create_update_reference(new_resource):
    assert len(new_resource.aggregations()) == 0
    new_resource.reference_create("reference", "http://studio.bakajo.com")
    assert len(new_resource.aggregations()) == 1
    aggregation = new_resource.aggregations()[0]
    assert len(aggregation.files()) == 1
    file = aggregation.files()[0]
    assert file.name == "reference.url"
    with tempfile.TemporaryDirectory() as tmp:
        new_resource.file_download(file, save_path=tmp)
        with open(os.path.join(tmp, file.name), "r") as f:
            assert "http://studio.bakajo.com" in str(f.read())

    new_resource.reference_update(
        new_resource.aggregations()[0].files()[0].name, "https://duckduckgo.com", refresh=False
    )

    with tempfile.TemporaryDirectory() as tmp:
        new_resource.file_download(new_resource.aggregations()[0].files()[0], save_path=tmp)
        with open(os.path.join(tmp, file.name), "r") as f:
            assert "https://duckduckgo.com" in str(f.read())


def test_file_unzip(new_resource):
    new_resource.file_upload("data/georaster_composite.zip")
    assert len(new_resource.files()) == 1
    assert len(new_resource.aggregations()) == 0
    new_resource.file_unzip(new_resource.files()[0])
    assert len(new_resource.aggregations()) == 1


def test_delete_file(new_resource):
    new_resource.file_upload("data/other.txt")
    assert len(new_resource.files()) == 1
    new_resource.file_delete(new_resource.files()[0])
    assert len(new_resource.files()) == 0


def test_access_rules(new_resource):
    ap = new_resource.access_permission
    pass


def test_refresh(resource):
    resource.metadata
    resource.files()
    resource.aggregations()

    assert resource._retrieved_map is not None
    assert resource._retrieved_metadata is not None
    assert resource._parsed_files is not None
    assert resource._parsed_aggregations is not None

    resource.refresh()

    assert resource._retrieved_map is None
    assert resource._retrieved_metadata is None
    assert resource._parsed_files is None
    assert resource._parsed_aggregations is None


def test_empty_creator(new_resource):
    new_resource.metadata.creators.clear()
    try:
        new_resource.save()
        assert False, "should have thrown error"
    except ValueError as e:
        assert "creators list must have at least one creator" in str(e)


def test_user_info(hydroshare):
    user = hydroshare.user(11)
    creator = Creator.from_user(user)
    assert creator.name == user.name
    assert creator.phone == user.phone
    assert creator.address == user.address
    assert creator.organization == user.organization
    assert creator.email == user.email
    assert creator.homepage == user.website
    assert creator.identifiers == user.identifiers
    assert creator.description == user.url.path

    contributor = Contributor.from_user(user)
    assert contributor.name == user.name
    assert contributor.phone == user.phone
    assert contributor.address == user.address
    assert contributor.organization == user.organization
    assert contributor.email == user.email
    assert contributor.homepage == user.website
    assert contributor.identifiers == user.identifiers


@pytest.mark.parametrize(
    "files",
    [
        ["logan1.tif", "logan2.tif", "logan.vrt", "logan_resmap.xml", "logan_meta.xml"],
        ["msf_version.refts.json", "msf_version.refts_resmap.xml", "msf_version.refts_meta.xml"],
        [
            "ODM2_Multi_Site_One_Variable.sqlite",
            "ODM2_Multi_Site_One_Variable_resmap.xml",
            "ODM2_Multi_Site_One_Variable_meta.xml",
        ],
        ["SWE_time.nc", "SWE_time_header_info.txt", "SWE_time_resmap.xml", "SWE_time_meta.xml"],
        ["test.xml", "test_resmap.xml", "test_meta.xml"],
        [
            "watersheds.shp",
            "watersheds.cpg",
            "watersheds.dbf",
            "watersheds.prj",
            "watersheds.sbn",
            "watersheds.sbx",
            "watersheds.shx",
            "watersheds_resmap.xml",
            "watersheds_meta.xml",
        ],
    ],
)
def test_aggregations(new_resource, files):
    root_path = "data/test_resource_metadata_files/"
    file_count = len(files) - 2  # exclude rdf/xml file
    new_resource.file_upload(*[os.path.join(root_path, file) for file in files])
    assert len(new_resource.aggregations()) == 1
    assert len(new_resource.files()) == 0
    agg = new_resource.aggregations()[0]
    agg_type = agg.metadata.type
    assert len(agg.files()) == file_count
    new_resource.aggregation_remove(agg)
    assert len(new_resource.aggregations()) == 0
    assert len(new_resource.files()) == file_count
    main_file = next(f for f in new_resource.files() if f.path.endswith(files[0]))
    assert main_file
    agg = new_resource.file_aggregate(main_file, agg_type)
    assert len(new_resource.aggregations()) == 1
    assert len(new_resource.files()) == 0
    assert len(agg.files()) == file_count
    with tempfile.TemporaryDirectory() as tmp:
        new_resource.aggregation_download(agg, tmp)
        files = os.listdir(tmp)
        assert len(files) == 1
    new_resource.aggregation_delete(agg)
    assert len(new_resource.aggregations()) == 0
    assert len(new_resource.files()) == 0


@pytest.mark.parametrize(
    "files",
    [
        [
            "asdf/testing.xml",
            "asdf/asdf_resmap.xml",
            "asdf/asdf_meta.xml",
        ],  # requires hydrosare updates in bag_ingestion_patches
    ],
)
def test_aggregation_fileset(new_resource, files):
    root_path = "data/test_resource_metadata_files/"
    file_count = len(files) - 2  # exclude rdf/xml file
    new_resource.folder_create("asdf", refresh=False)
    new_resource.file_upload(*[os.path.join(root_path, file) for file in files], destination_path="asdf")
    assert len(new_resource.aggregations()) == 1
    assert len(new_resource.files()) == 0
    agg = new_resource.aggregations()[0]
    agg_type = agg.metadata.type
    assert len(agg.files()) == file_count
    new_resource.aggregation_remove(agg)
    assert len(new_resource.aggregations()) == 0
    assert len(new_resource.files()) == file_count
    main_file = next(f for f in new_resource.files() if f.path.endswith(files[0]))
    assert main_file
    agg = new_resource.file_aggregate(main_file, agg_type=agg_type)
    assert len(new_resource.aggregations()) == 1
    assert len(new_resource.files()) == 0
    assert len(agg.files()) == file_count
    with tempfile.TemporaryDirectory() as tmp:
        new_resource.aggregation_download(agg, tmp)
        files = os.listdir(tmp)
        assert len(files) == 1
    new_resource.aggregation_delete(agg)
    assert len(new_resource.aggregations()) == 0
    assert len(new_resource.files()) == 0


def test_pandas_series_local(timeseries_resource):
    timeseries_resource.refresh()
    timeseries = timeseries_resource.aggregation(type=AggregationType.TimeSeriesAggregation)
    series_result = next(
        r for r in timeseries.metadata.time_series_results if r.series_id == "2837b7d9-1ebc-11e6-a16e-f45c8999816f"
    )
    series = timeseries.as_series(series_result.series_id, "data/test_resource_metadata_files")
    assert len(series) == 1333


def test_pandas_series_remote(timeseries_resource):
    timeseries_resource.refresh()
    timeseries = timeseries_resource.aggregation(type=AggregationType.TimeSeriesAggregation)
    series_result = next(
        r for r in timeseries.metadata.time_series_results if r.series_id == "3b9037f8-1ebc-11e6-a304-f45c8999816f"
    )
    series_map = timeseries.as_series(series_result.series_id)
    assert len(series_map) == 1440


def test_folder_zip(new_resource):
    new_resource.folder_create("test_folder", refresh=False)
    new_resource.file_upload("data/other.txt", destination_path="test_folder", refresh=False)
    new_resource.file_zip("test_folder")
    assert new_resource.file().path == "test_folder.zip"
    assert not new_resource.file(path="data/other.txt")


def test_folder_zip_specify_name(new_resource):
    new_resource.folder_create("test_folder", refresh=False)
    new_resource.file_upload("data/other.txt", destination_path="test_folder", refresh=False)
    new_resource.file_zip("test_folder", "test.zip", False)
    assert new_resource.file(path="test.zip").path == "test.zip"
    assert new_resource.file(path="test_folder/other.txt").path == "test_folder/other.txt"


def test_folder_rename(new_resource):
    new_resource.folder_create("test_folder", refresh=False)
    new_resource.file_upload("data/other.txt", destination_path="test_folder", refresh=False)
    new_resource.folder_rename("test_folder", "renamed_folder")
    assert new_resource.file(path="renamed_folder/other.txt")


def test_folder_delete(new_resource):
    new_resource.folder_create("test_folder", refresh=False)
    new_resource.file_upload("data/other.txt", destination_path="test_folder")
    assert len(new_resource.files()) == 1
    new_resource.folder_delete("test_folder")
    assert not new_resource.file()


def test_zipped_file_download(resource):
    with tempfile.TemporaryDirectory() as tmp:
        bag = resource.file_download("other.txt", zipped=True, save_path=tmp)
        assert os.path.exists(bag)
        assert bag.endswith(".zip")


def test_folder_download(new_resource):
    new_resource.folder_create("test_folder", refresh=False)
    new_resource.file_upload("data/other.txt", destination_path="test_folder")
    assert len(new_resource.files()) == 1
    with tempfile.TemporaryDirectory() as td:
        downloaded_folder = new_resource.folder_download("test_folder", save_path=td)
        assert os.path.basename(downloaded_folder) == "test_folder.zip"


# @pytest.mark.skip("Requires hydroshare update to url encode resourcemap urls")
def test_filename_spaces(hydroshare):
    res = hydroshare.create()
    res.folder_create("with spaces", refresh=False)
    res.file_upload("data/other.txt", destination_path="with spaces", refresh=False)
    res.file_rename("with spaces/other.txt", "with spaces/with spaces file.txt")
    file = res.file(path="with spaces/with spaces file.txt")
    with tempfile.TemporaryDirectory() as td:
        filename = res.file_download(file, save_path=td)
        assert os.path.basename(filename) == "with spaces file.txt"


def test_copy(new_resource):
    try:
        res_copy = new_resource.copy()
        assert res_copy.metadata.title == new_resource.metadata.title
        assert res_copy.resource_id != new_resource.resource_id
    finally:
        res_copy.delete()


def test_resource_version(new_resource):
    try:
        res_version = new_resource.new_version()
        assert res_version.metadata.title == new_resource.metadata.title
        assert res_version.resource_id != new_resource.resource_id
        version_of = next(
            relation.value for relation in res_version.metadata.relations if relation.type == RelationType.isVersionOf
        )
        version_of = version_of.split("/")[-1]
        assert version_of == new_resource.resource_id
    finally:
        res_version.delete()


def test_resource_public(resource):
    assert resource.system_metadata()['public'] is False
    resource.set_sharing_status(public=True)
    assert resource.system_metadata()['public'] is True
