import json

from hsmodels.schemas.enums import AggregationType

from hsclient.hydroshare import Aggregation
from hsclient.schema.legacy.raster import BandInformation, BoxCoverage, CellInformation, GeographicRasterMetadata


class DummyS3Client:
    def __init__(self):
        self.writes = []

    def write_text(self, path, text):
        self.writes.append((path, text))


def test_raster_metadata_can_be_edited_in_legacy_format_and_saved_as_schema_org():
    s3_client = DummyS3Client()
    raster_aggr = Aggregation(
        "bucket-name/123/.hsjsonld/raster-folder/logan.vrt.json",
        hs_session=None,
        s3_client=s3_client,
    )

    raster_aggr._retrieved_metadata = GeographicRasterMetadata(
        type=AggregationType.GeographicRasterAggregation,
        title="Original Raster",
    )
    raster_aggr._main_file_path = "raster-folder/logan.vrt"

    # Raster metadata should be editable through the legacy model.
    assert isinstance(raster_aggr.metadata, GeographicRasterMetadata)

    raster_aggr.metadata.title = "Edited Legacy Raster Metadata"
    raster_aggr.metadata.subjects = ["legacy", "raster", "editing"]
    raster_aggr.metadata.additional_metadata = {"processing_level": "L2"}
    # TODO: Maybe we shouldn't allow editing of extracted metadata
    raster_aggr.metadata.spatial_coverage = BoxCoverage(
        name="Cache Valley",
        northlimit=42.0,
        eastlimit=-111.0,
        southlimit=41.5,
        westlimit=-111.5,
        units="Decimal degrees",
        projection="WGS 84 EPSG:4326",
        type="box",
    )
    raster_aggr.metadata.band_information = BandInformation(
        name="Band 1",
        variable_name="Band 1",
        variable_unit="m",
        minimum_value="0",
        maximum_value="100",
        no_data_value="-9999",
        comment="Updated from legacy model",
    )
    raster_aggr.metadata.cell_information = CellInformation(
        rows=100,
        columns=200,
        cell_size_x_value=10.0,
        cell_size_y_value=10.0,
        cell_data_type="float32",
    )

    raster_aggr.save(refresh=False)

    assert len(s3_client.writes) == 1
    path, text = s3_client.writes[0]
    assert path.endswith(".hsmetadata/raster-folder/logan.vrt.user_metadata.json")

    saved_metadata = json.loads(text)

    # Saved payload should be schema.org ScientificDataset JSON-LD.
    assert saved_metadata["@type"] == "ScientificDataset"
    assert saved_metadata["additionalType"] == "GeographicRaster"
    assert saved_metadata["name"] == "Edited Legacy Raster Metadata"
    assert saved_metadata["keywords"] == ["legacy", "raster", "editing"]

    assert saved_metadata["spatialCoverage"]["@type"] == "Place"
    assert saved_metadata["spatialCoverage"]["geo"]["@type"] == "GeoShape"
    # Box token order is "S W N E" (south, west, north, east)
    assert saved_metadata["spatialCoverage"]["geo"]["box"] == "41.5 -111.5 42.0 -111.0"

    assert saved_metadata["variableMeasured"][0]["@type"] == "DataVariable"
    assert saved_metadata["variableMeasured"][0]["name"] == "Band 1"
    assert saved_metadata["variableMeasured"][0]["unit"] == "m"

    # Legacy keys should not be written to the saved JSON payload.
    assert "spatial_coverage" not in saved_metadata
    assert "band_information" not in saved_metadata
    assert "cell_information" not in saved_metadata
