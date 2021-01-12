import pytest
import tempfile
import os

from hs_rdf.hydroshare import HydroShare, AggregationType
from hs_rdf.schemas.enums import RelationType
from hs_rdf.schemas.fields import Relation, Creator, Contributor


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
    new_resource.files()[0].unzip()
    new_resource.refresh()
    return new_resource

@pytest.fixture()
def timeseries_resource(new_resource):
    files = ["ODM2_Multi_Site_One_Variable.sqlite", "ODM2_Multi_Site_One_Variable_resmap.xml", "ODM2_Multi_Site_One_Variable_meta.xml"]
    root_path = "data/test_resource_metadata_files/"
    new_resource.upload(*[root_path + file for file in files])
    new_resource.refresh()
    return new_resource

def test_filtering_aggregations(timeseries_resource):
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
    assert timeseries_resource.aggregation(title="changed from the Little Bear River, UT").metadata.title == "changed from the Little Bear River, UT"

    assert len(timeseries_resource.aggregations(period_coverage__name="period_coverage name",
                                                title="changed from the Little Bear River, UT")) == 1
    assert timeseries_resource.aggregation(period_coverage__name="period_coverage name",
                                           title="changed from the Little Bear River, UT").metadata.period_coverage.name == "period_coverage name"

    assert len(timeseries_resource.aggregations(period_coverage__name="period_coverage name",
                                                title="bad")) == 0

    assert not timeseries_resource.aggregation(period_coverage__name="bad")
    assert len(timeseries_resource.aggregations(period_coverage__name="bad")) == 0

    assert len(timeseries_resource.aggregations(bad="does not matter")) == 0
    assert not timeseries_resource.aggregation(bad="does not matter")

def test_filtering_aggregations_by_files(timeseries_resource):
    assert len(timeseries_resource.aggregations(file__path="ODM2_Multi_Site_One_Variable.sqlite")) == 1
    assert timeseries_resource.aggregation(file__path="ODM2_Multi_Site_One_Variable.sqlite")
    assert len(timeseries_resource.aggregations(files__path="ODM2_Multi_Site_One_Variable.sqlite")) == 1
    assert timeseries_resource.aggregation(files__path="ODM2_Multi_Site_One_Variable.sqlite")

    assert len(timeseries_resource.aggregations(file__path="No_match.sqlite")) == 0
    assert not timeseries_resource.aggregation(file__path="No_match.sqlite")
    assert len(timeseries_resource.aggregations(files__path="No_match.sqlite")) == 0
    assert not timeseries_resource.aggregation(files__path="No_match.sqlite")

def test_filtering_files(resource):
    resource.create_folder("asdf")
    resource.upload("data/test_resource_metadata_files/asdf/testing.xml", dest_relative_path="asdf")
    resource.create_folder("referenced_time_series")
    resource.upload("data/test_resource_metadata_files/msf_version.refts.json", dest_relative_path="referenced_time_series")
    resource.refresh()

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
    res = new_resource#hydroshare.resource("1248abc1afc6454199e65c8f642b99a0")
    res.metadata.creators.append(Creator(name="Testing"))
    res.save()
    res.refresh()
    assert res.metadata.creators[0].name == "Black, Scott S"
    assert res.metadata.creators[1].name == "Testing"
    reversed = [res.metadata.creators[1], res.metadata.creators[0]]
    res.metadata.creators = reversed
    res.save()
    res.refresh()
    assert res.metadata.creators[1].name == "Black, Scott S"
    assert res.metadata.creators[0].name == "Testing"

def test_resource_metadata_updating(new_resource):

    assert len(new_resource.metadata.subjects) == 0

    new_resource.metadata.subjects = ['sub1', 'sub2']
    new_resource.metadata.title = "resource test"
    new_resource.metadata.additional_metadata = {"key1": "value1", "key2": "value2", "key3": "value3"}
    new_resource.metadata.abstract = "world’s"
    new_resource.metadata.relations = [Relation(type=RelationType.isCopiedFrom, value="is hosted by value")]

    new_resource.save()
    new_resource.refresh()

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
    except Exception as e:
        assert str(e) == "failed to retrieve {}".format(res._map_url)

def test_files_aggregations(resource):
    assert len(resource.files()) == 1
    assert len(resource.aggregations()) == 1
    assert len(resource.aggregations()[0].files()) == 3
    assert len(resource.aggregations()[0].aggregations()) == 0

def test_resource_download(new_resource):
    with tempfile.TemporaryDirectory() as tmp:
        bag = new_resource.download(tmp)
        assert os.path.exists(bag)
        assert bag.endswith(".zip")

def test_file_download(resource):
    with tempfile.TemporaryDirectory() as tmp:
        file = resource.files()[0]
        downloaded_file = file.download(tmp)
        assert os.path.exists(downloaded_file)
        assert os.path.basename(downloaded_file) == file.name

def test_aggregation_download(resource):
    assert len(resource.aggregations()) == 1
    agg = resource.aggregations()[0]
    with tempfile.TemporaryDirectory() as tmp:
        agg.download(tmp)
        files = os.listdir(tmp)
        assert len(files) == 1
        assert files[0] == "logan.vrt.zip"

def test_aggregation_delete(resource):
    assert len(resource.aggregations()) == 1
    assert len(resource.files()) == 1
    agg = resource.aggregations()[0]
    agg.delete()
    resource.refresh()
    assert len(resource.aggregations()) == 0
    assert len(resource.files()) == 1

def test_aggregation_remove(resource):
    assert len(resource.aggregations()) == 1
    assert len(resource.files()) == 1
    agg = resource.aggregations()[0]
    agg.remove()
    resource.refresh()
    assert len(resource.aggregations()) == 0
    assert len(resource.files()) == 4

def test_file_upload_and_rename(new_resource):
    assert len(new_resource.files()) == 0
    new_resource.upload("data/other.txt")
    new_resource.refresh()
    assert len(new_resource.files()) == 1
    file = new_resource.files()[0]
    file.rename("updated.txt")
    new_resource.refresh()
    assert new_resource.files()[0].name == "updated.txt"

def test_file_aggregate(new_resource):
    assert len(new_resource.files()) == 0
    new_resource.create_folder("folder")
    new_resource.upload("data/other.txt", dest_relative_path="folder")
    new_resource.refresh()
    assert len(new_resource.files()) == 1
    new_resource.files()[0].aggregate(AggregationType.SingleFileAggregation)
    new_resource.refresh()
    assert len(new_resource.files()) == 0
    assert len(new_resource.aggregations()) == 1
    assert len(new_resource.aggregations()[0].files()) == 1

def test_create_update_reference(new_resource):
    assert len(new_resource.aggregations()) == 0
    new_resource.create_reference("reference", "http://studio.bakajo.com")
    new_resource.refresh()
    assert len(new_resource.aggregations()) == 1
    aggregation = new_resource.aggregations()[0]
    assert len(aggregation.files()) == 1
    file = aggregation.files()[0]
    assert file.name == "reference.url"
    with tempfile.TemporaryDirectory() as tmp:
        file.download(tmp)
        with open(os.path.join(tmp, file.name), "r") as f:
            assert "http://studio.bakajo.com" in str(f.read())

    new_resource.update_reference(new_resource.aggregations()[0].files()[0].name, "https://duckduckgo.com")

    with tempfile.TemporaryDirectory() as tmp:
        new_resource.aggregations()[0].files()[0].download(tmp)
        with open(os.path.join(tmp, file.name), "r") as f:
            assert "https://duckduckgo.com" in str(f.read())

def test_file_unzip(new_resource):
    new_resource.upload("data/georaster_composite.zip")
    new_resource.refresh()
    assert len(new_resource.files()) == 1
    assert len(new_resource.aggregations()) == 0
    new_resource.files()[0].unzip()
    new_resource.refresh()
    assert len(new_resource.aggregations()) == 1

def test_delete_file(new_resource):
    new_resource.upload("data/other.txt")
    new_resource.refresh()
    assert len(new_resource.files()) == 1
    new_resource.files()[0].delete()
    new_resource.refresh()
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

@pytest.mark.parametrize("files", [
    ["logan1.tif", "logan2.tif", "logan.vrt", "logan_resmap.xml", "logan_meta.xml"],
    ["msf_version.refts.json", "msf_version.refts_resmap.xml", "msf_version.refts_meta.xml"],
    ["ODM2_Multi_Site_One_Variable.sqlite", "ODM2_Multi_Site_One_Variable_resmap.xml", "ODM2_Multi_Site_One_Variable_meta.xml"],
    ["SWE_time.nc", "SWE_time_header_info.txt", "SWE_time_resmap.xml", "SWE_time_meta.xml"],
    ["test.xml", "test_resmap.xml", "test_meta.xml"],
    ["watersheds.shp", "watersheds.cpg", "watersheds.dbf", "watersheds.prj", "watersheds.sbn", "watersheds.sbx",
     "watersheds.shx", "watersheds_resmap.xml", "watersheds_meta.xml"]
])
def test_aggregations(new_resource, files):
    root_path = "data/test_resource_metadata_files/"
    file_count = len(files) - 2 # exclude rdf/xml file
    new_resource.upload(*[root_path + file for file in files])
    new_resource.refresh()
    assert len(new_resource.aggregations()) == 1
    assert len(new_resource.files()) == 0
    agg = new_resource.aggregations()[0]
    agg_type = agg.metadata.type
    assert len(agg.files()) == file_count
    agg.remove()
    new_resource.refresh()
    assert len(new_resource.aggregations()) == 0
    assert len(new_resource.files()) == file_count
    main_file = next(f for f in new_resource.files() if f.relative_path.endswith(files[0]))
    assert main_file
    main_file.aggregate(agg_type)
    new_resource.refresh()
    assert len(new_resource.aggregations()) == 1
    assert len(new_resource.files()) == 0
    agg = new_resource.aggregations()[0]
    assert len(agg.files()) == file_count
    with tempfile.TemporaryDirectory() as tmp:
        agg.download(tmp)
        files = os.listdir(tmp)
        assert len(files) == 1
    agg.delete()
    new_resource.refresh()
    assert len(new_resource.aggregations()) == 0
    assert len(new_resource.files()) == 0


@pytest.mark.parametrize("files", [
    ["asdf/testing.xml", "asdf/asdf_resmap.xml", "asdf/asdf_meta.xml"], # requires hydrosare updates in bag_ingestion_patches
])
def test_aggregation_fileset(new_resource, files):
    root_path = "data/test_resource_metadata_files/"
    file_count = len(files) - 2 # exclude rdf/xml file
    new_resource.create_folder("asdf")
    new_resource.upload(*[root_path + file for file in files], dest_relative_path="asdf")
    new_resource.refresh()
    assert len(new_resource.aggregations()) == 1
    assert len(new_resource.files()) == 0
    agg = new_resource.aggregations()[0]
    agg_type = agg.metadata.type
    assert len(agg.files()) == file_count
    agg.remove()
    new_resource.refresh()
    assert len(new_resource.aggregations()) == 0
    assert len(new_resource.files()) == file_count
    main_file = next(f for f in new_resource.files() if f.relative_path.endswith(files[0]))
    assert main_file
    main_file.aggregate(agg_type)
    new_resource.refresh()
    assert len(new_resource.aggregations()) == 1
    assert len(new_resource.files()) == 0
    agg = new_resource.aggregations()[0]
    assert len(agg.files()) == file_count
    with tempfile.TemporaryDirectory() as tmp:
        agg.download(tmp)
        files = os.listdir(tmp)
        assert len(files) == 1
    agg.delete()
    new_resource.refresh()
    assert len(new_resource.aggregations()) == 0
    assert len(new_resource.files()) == 0

def test_pandas_series_local(timeseries_resource):
    timeseries = timeseries_resource.aggregation(type=AggregationType.TimeSeriesAggregation)
    series_map = timeseries.as_series("data/test_resource_metadata_files")
    assert len(series_map) == 7

def test_pandas_series_remote(timeseries_resource):
    timeseries = timeseries_resource.aggregation(type=AggregationType.TimeSeriesAggregation)
    series_map = timeseries.as_series()
    assert len(series_map) == 7
