import json
from datetime import datetime

from hsmodels.schemas.enums import AggregationType

from hsclient.hydroshare import Aggregation
from hsclient.schema.legacy.netcdf import BoxCoverage, MultidimensionalMetadata, PeriodCoverage, Variable


class DummyS3Client:
    def __init__(self):
        self.writes = []

    def write_text(self, path, text):
        self.writes.append((path, text))


def test_netcdf_metadata_can_be_edited_in_legacy_format_and_saved_as_schema_org():
    s3_client = DummyS3Client()
    netcdf_aggr = Aggregation(
        "bucket-name/123/.hsjsonld/netcdf-folder/climate_data.nc.json",
        hs_session=None,
        s3_client=s3_client,
    )

    netcdf_aggr._retrieved_metadata = MultidimensionalMetadata(
        type=AggregationType.MultidimensionalAggregation,
        title="Original NetCDF",
    )
    netcdf_aggr._main_file_path = "netcdf-folder/climate_data.nc"

    # NetCDF metadata should be editable through the legacy model.
    assert isinstance(netcdf_aggr.metadata, MultidimensionalMetadata)

    netcdf_aggr.metadata.title = "Edited Legacy NetCDF Metadata"
    netcdf_aggr.metadata.subjects = ["legacy", "netcdf", "editing"]
    netcdf_aggr.metadata.additional_metadata = {"processing_level": "L3"}
    # TODO: Maybe we shouldn't allow editing of extracted metadata
    netcdf_aggr.metadata.spatial_coverage = BoxCoverage(
        name="Utah Valley",
        northlimit=40.5,
        eastlimit=-111.5,
        southlimit=40.0,
        westlimit=-112.0,
        units="Decimal degrees",
        projection="WGS 84 EPSG:4326",
        type="box",
    )
    netcdf_aggr.metadata.period_coverage = PeriodCoverage(
        start=datetime(2020, 1, 1),
        end=datetime(2021, 12, 31),
    )
    netcdf_aggr.metadata.variables = [
        Variable(
            name="temperature",
            unit="degC",
            type="Float",
            shape="time lat lon",
            descriptive_name="Air Temperature at 2m",
            method="Direct Measurement",
            missing_value="-9999",
        ),
        Variable(
            name="precipitation",
            unit="mm",
            type="Float",
            shape="time lat lon",
            descriptive_name="Daily Precipitation",
            missing_value="-9999",
        ),
    ]

    netcdf_aggr.save(refresh=False)

    assert len(s3_client.writes) == 1
    path, text = s3_client.writes[0]
    assert path.endswith(".hsmetadata/netcdf-folder/climate_data.nc.user_metadata.json")

    saved_metadata = json.loads(text)

    # Saved payload should be schema.org ScientificDataset JSON-LD.
    assert saved_metadata["@type"] == "ScientificDataset"
    assert saved_metadata["additionalType"] == "MultiDimensional"
    assert saved_metadata["name"] == "Edited Legacy NetCDF Metadata"
    assert saved_metadata["keywords"] == ["legacy", "netcdf", "editing"]

    # additional_metadata should be preserved as additionalProperty entries.
    additional_props = {p["name"]: p["value"] for p in saved_metadata["additionalProperty"]}
    assert additional_props["processing_level"] == "L3"

    # Spatial coverage should be encoded as a schema.org Place with a GeoShape box.
    assert saved_metadata["spatialCoverage"]["@type"] == "Place"
    assert saved_metadata["spatialCoverage"]["geo"]["@type"] == "GeoShape"
    # Box token order is "S W N E" (south, west, north, east)
    assert saved_metadata["spatialCoverage"]["geo"]["box"] == "40.0 -112.0 40.5 -111.5"

    # Temporal coverage should carry start and end dates.
    assert saved_metadata["temporalCoverage"]["startDate"].startswith("2020-01-01")
    assert saved_metadata["temporalCoverage"]["endDate"].startswith("2021-12-31")

    # Variables should be encoded as DataVariable entries under variableMeasured.
    assert len(saved_metadata["variableMeasured"]) == 2

    temp_var = saved_metadata["variableMeasured"][0]
    assert temp_var["@type"] == "DataVariable"
    assert temp_var["name"] == "temperature"
    assert temp_var["unit"] == "degC"
    assert temp_var["noDataValue"] == "-9999"

    precip_var = saved_metadata["variableMeasured"][1]
    assert precip_var["@type"] == "DataVariable"
    assert precip_var["name"] == "precipitation"
    assert precip_var["unit"] == "mm"

    assert temp_var["description"] == "Air Temperature at 2m"
    assert temp_var["method"] == "Direct Measurement"
    assert precip_var["description"] == "Daily Precipitation"
