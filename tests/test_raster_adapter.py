import json

import pytest
from hsmodels.schemas.enums import AggregationType
from pydantic import ValidationError

from hsclient.schema.legacy.raster import (
    BandInformation,
    BoxCoverage,
    BoxSpatialReference,
    CellInformation,
    GeographicRasterMetadata,
    PeriodCoverage,
    Rights,
)

from hsclient.hydroshare import Aggregation
from hsclient.metadata_adapter.adapter import MetadataAdapter
from hsclient.schema.dataset import ScientificDataset
from hsclient.schema.utils import load_json


class DummyS3Client:
    def __init__(self):
        self.writes = []

    def write_text(self, path, text):
        self.writes.append((path, text))


def _schemaorg_raster_metadata_dict():
    return {
        "@context": "https://hydroshare.org/schema",
        "@type": "ScientificDataset",
        "additionalType": "GeographicRaster",
        "name": "Raster Dataset",
        "description": "Raster dataset description",
        "keywords": ["raster", "elevation"],
        "inLanguage": "eng",
        "spatialCoverage": {
            "@type": "Place",
            "name": "Cache Valley",
            "geo": {"@type": "GeoShape", "box": "42.0 -111.0 41.5 -111.5"},
            "srs": {
                "@type": "SpatialReference",
                "name": "WGS 84",
                "srsType": "geographic",
                "code": "EPSG:4326",
                "wktString": "GEOGCS[\"WGS 84\"]",
            },
        },
        "temporalCoverage": {
            "startDate": "2024-01-01T00:00:00",
            "endDate": "2024-01-31T00:00:00",
        },
        "variableMeasured": [
            {
                "@type": "DataVariable",
                "name": "Band 1",
                "dimensions": ["rows", "columns"],
                "description": "Primary raster band",
                "dataType": "float32",
                "unit": "m",
                "minValue": 0,
                "maxValue": 100,
                "noDataValue": -9999,
            }
        ],
        "dimensions": [
            {"@type": "Dimension", "name": "rows", "shape": 100},
            {"@type": "Dimension", "name": "columns", "shape": 200},
        ],
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "cell_size_x_value", "value": "10"},
            {"@type": "PropertyValue", "name": "cell_size_y_value", "value": "10"},
            {"@type": "PropertyValue", "name": "cell_data_type", "value": "float32"},
            {"@type": "PropertyValue", "name": "custom_meta", "value": "custom_value"},
        ],
        "license": {"@type": "CreativeWork", "name": "CC-BY-4.0", "url": "https://example.com/license"},
    }


def _legacy_raster_metadata():
    return GeographicRasterMetadata.model_construct(
        title="Legacy Raster",
        subjects=["raster", "legacy"],
        language="eng",
        description="Legacy description",
        additional_metadata={"custom_meta": "custom_value"},
        spatial_coverage=BoxCoverage.model_construct(
            type="box",
            name="Cache Valley",
            northlimit=42.0,
            eastlimit=-111.0,
            southlimit=41.5,
            westlimit=-111.5,
            units="Decimal degrees",
            projection="WGS 84 EPSG:4326",
        ),
        period_coverage=PeriodCoverage.model_construct(start="2024-01-01T00:00:00", end="2024-01-31T00:00:00"),
        band_information=BandInformation.model_construct(
            name="Band 1",
            variable_name="Band 1",
            variable_unit="m",
            no_data_value="-9999",
            minimum_value="0",
            maximum_value="100",
            comment="Primary raster band",
        ),
        spatial_reference=BoxSpatialReference.model_construct(
            type="box",
            name="WGS 84",
            northlimit=42.0,
            eastlimit=-111.0,
            southlimit=41.5,
            westlimit=-111.5,
            units="Decimal degrees",
            projection="WGS 84 EPSG:4326",
            projection_string="GEOGCS[\"WGS 84\"]",
            projection_string_type="EPSG:4326",
            projection_name="WGS 84",
        ),
        cell_information=CellInformation.model_construct(
            rows=100,
            columns=200,
            cell_size_x_value=10.0,
            cell_size_y_value=10.0,
            cell_data_type="float32",
        ),
        type=AggregationType.GeographicRasterAggregation,
        url="https://www.hydroshare.org/resource/legacy-raster",
        rights=Rights.model_construct(statement="CC-BY-4.0", url="https://example.com/license"),
    )


def test_schema_to_legacy_raster_conversion_returns_geographic_raster_metadata():
    legacy = MetadataAdapter.to_legacy_geographic_raster_metadata(_schemaorg_raster_metadata_dict())

    assert isinstance(legacy, GeographicRasterMetadata)
    assert legacy.title == "Raster Dataset"
    assert legacy.subjects == ["raster", "elevation"]
    assert legacy.language == "eng"
    assert legacy.additional_metadata["custom_meta"] == "custom_value"
    assert legacy.description == "Raster dataset description"
    assert legacy.band_information.name == "Band 1"
    assert legacy.cell_information.rows == 100
    assert legacy.cell_information.columns == 200
    assert legacy.url is None
    assert legacy.rights.statement == "CC-BY-4.0"


def test_legacy_to_schema_raster_conversion_returns_scientific_dataset():
    dataset = MetadataAdapter.to_geographic_raster_metadata(_legacy_raster_metadata())

    assert isinstance(dataset, ScientificDataset)
    assert dataset.additionalType.value == "GeographicRaster"
    assert dataset.name == "Legacy Raster"
    assert dataset.description == "Legacy description"
    assert dataset.keywords == ["raster", "legacy"]
    assert str(dataset.url) == "https://www.hydroshare.org/resource/legacy-raster"
    assert dataset.license.name == "CC-BY-4.0"
    assert str(dataset.license.url) == "https://example.com/license"
    assert dataset.spatialCoverage.geo.box == "42.0 -111.0 41.5 -111.5"
    assert dataset.variableMeasured[0].name == "Band 1"


def test_load_json_routes_raster_aggregation_through_schema_to_legacy_adapter():
    result = load_json(_schemaorg_raster_metadata_dict(), "123/.hsjsonld/raster-folder/logan.vrt.json")

    assert isinstance(result, GeographicRasterMetadata)
    assert result.type == AggregationType.GeographicRasterAggregation
    assert result.title == "Raster Dataset"


def test_aggregation_save_uses_legacy_to_schema_adapter_for_raster_metadata():
    s3_client = DummyS3Client()
    aggregation = Aggregation(
        "bucket-name/123/.hsjsonld/raster-folder/logan.vrt.json",
        hs_session=None,
        s3_client=s3_client,
    )
    aggregation._retrieved_metadata = _legacy_raster_metadata()
    aggregation._main_file_path = "raster-folder/logan.vrt"

    aggregation.save(refresh=False)

    assert len(s3_client.writes) == 1
    _, metadata_json = s3_client.writes[0]
    metadata = json.loads(metadata_json)
    assert metadata["@type"] == "ScientificDataset"
    assert metadata["additionalType"] == "GeographicRaster"
    assert metadata["name"] == "Legacy Raster"
    assert metadata["url"] == "https://www.hydroshare.org/resource/legacy-raster"


def test_schema_to_legacy_raster_partial_fields_use_fallbacks_without_failure():
    partial_metadata = {
        "@context": "https://hydroshare.org/schema",
        "@type": "ScientificDataset",
        "additionalType": "GeographicRaster",
    }

    legacy = MetadataAdapter.to_legacy_geographic_raster_metadata(partial_metadata)

    assert isinstance(legacy, GeographicRasterMetadata)
    assert legacy.language is None
    assert legacy.url is None
    assert legacy.band_information is None


def test_non_raster_scientific_dataset_remains_passthrough_in_load_json():
    non_raster_metadata = {
        "@context": "https://hydroshare.org/schema",
        "@type": "ScientificDataset",
        "additionalType": "Tabular",
        "name": "CSV Dataset",
    }

    result = load_json(non_raster_metadata, "123/.hsjsonld/tabular-folder/data.csv.json")

    assert isinstance(result, ScientificDataset)
    assert result.additionalType.value == "Tabular"
    assert result.name == "CSV Dataset"


def test_multi_band_round_trip_is_supported():
    schema_metadata = _schemaorg_raster_metadata_dict()
    schema_metadata["variableMeasured"] = [
        {
            "@type": "DataVariable",
            "name": "Band 1",
            "dimensions": ["rows", "columns"],
            "unit": "m",
            "minValue": 0,
            "maxValue": 100,
            "noDataValue": -9999,
        },
        {
            "@type": "DataVariable",
            "name": "Band 2",
            "dimensions": ["rows", "columns"],
            "unit": "m",
            "minValue": 10,
            "maxValue": 200,
            "noDataValue": -9999,
        },
    ]

    legacy = MetadataAdapter.to_legacy_geographic_raster_metadata(schema_metadata)
    assert isinstance(legacy.band_information, list)
    assert len(legacy.band_information) == 2

    round_tripped = MetadataAdapter.to_geographic_raster_metadata(legacy)
    assert len(round_tripped.variableMeasured) == 2
    assert round_tripped.variableMeasured[0].name == "Band 1"
    assert round_tripped.variableMeasured[1].name == "Band 2"
    assert round_tripped.dimensions[0].name == "band"
    assert round_tripped.dimensions[0].shape == 2


def test_schema_to_legacy_spatial_reference_does_not_invent_units_or_projection_when_missing_srs():
    schema_metadata = _schemaorg_raster_metadata_dict()
    schema_metadata["spatialCoverage"].pop("srs")

    legacy = MetadataAdapter.to_legacy_geographic_raster_metadata(schema_metadata)

    assert isinstance(legacy.spatial_reference, BoxSpatialReference)
    assert legacy.spatial_reference.units is None
    assert legacy.spatial_reference.projection is None
    assert legacy.spatial_reference.projection_name is None
    assert legacy.spatial_reference.projection_string_type is None


def test_legacy_to_schema_spatial_reference_uses_neutral_name_when_projection_missing():
    legacy = _legacy_raster_metadata()
    legacy.spatial_reference = BoxSpatialReference.model_construct(
        type="box",
        name="Cache Valley",
        northlimit=42.0,
        eastlimit=-111.0,
        southlimit=41.5,
        westlimit=-111.5,
        units=None,
        projection=None,
        projection_string=None,
        projection_string_type=None,
        projection_name=None,
    )

    dataset = MetadataAdapter.to_geographic_raster_metadata(legacy)

    assert dataset.spatialCoverage.srs.name == "Unknown spatial reference"
    assert dataset.spatialCoverage.srs.srsType == "geographic"


def test_legacy_raster_rights_requires_statement_or_url():
    with pytest.raises(ValidationError, match="Either 'statement' or 'url' must have a value"):
        Rights()


def test_legacy_raster_rights_accepts_url_only():
    rights = Rights(url="https://example.com/license")
    assert str(rights.url) == "https://example.com/license"
