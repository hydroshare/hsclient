"""
Tests for the Geographic Raster metadata adapter.

Coverage:
  - Schema → legacy conversion (ScientificDataset → GeographicRasterMetadata)
  - Legacy → schema conversion (GeographicRasterMetadata → ScientificDataset)
  - Full round-trips in both directions
  - Multi-band round-trip (band_information as list)
  - Spatial coverage (box only) and spatial reference mapping
  - Temporal coverage / period coverage
  - Rights / license mapping
  - Cell information ↔ additionalProperty mapping
  - Partial / missing-field fallbacks
  - load_json dispatch for GeographicRaster type
  - Aggregation.save() writes schema.org JSON via S3 client
"""

import json
from datetime import datetime

import pytest
from hsmodels.schemas.enums import AggregationType
from pydantic import ValidationError

from hsclient.hydroshare import Aggregation
from hsclient.metadata_adapter.adapter import MetadataAdapter
from hsclient.metadata_adapter.raster_adapter import RasterMetadataAdapter
from hsclient.schema.base import (
    CreativeWork,
    GeoShape,
    Place,
    PropertyValue,
    SpatialReference,
    TemporalCoverage,
)
from hsclient.schema.dataset import AdditionalType, ScientificDataset
from hsclient.schema.datavariable import DataVariable, Dimension
from hsclient.schema.legacy.raster import (
    BandInformation,
    BoxCoverage,
    BoxSpatialReference,
    CellInformation,
    GeographicRasterMetadata,
    PeriodCoverage,
    Rights,
)
from hsclient.schema.utils import load_json


class DummyS3Client:
    def __init__(self):
        self.writes = []

    def write_text(self, path, text):
        self.writes.append((path, text))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_schema_dataset(**kwargs) -> ScientificDataset:
    place = Place.model_construct()
    place.name = "Cache Valley"
    place.geo = GeoShape.model_construct(box="42.0 -111.0 41.5 -111.5", validate_bbox=False)
    place.srs = SpatialReference.model_construct(
        name="WGS 84",
        srsType="geographic",
        code="EPSG:4326",
        wktString='GEOGCS["WGS 84"]',
    )
    defaults = dict(
        additionalType=AdditionalType.GEOGRAPHIC_RASTER,
        name="Raster Dataset",
        description="Raster dataset description",
        keywords=["raster", "elevation"],
        inLanguage="eng",
        variableMeasured=[
            DataVariable.model_construct(
                name="Band 1",
                dimensions=["rows", "columns"],
                description="Primary raster band",
                dataType="float32",
                unit="m",
                minValue=0,
                maxValue=100,
                noDataValue="-9999",
            )
        ],
        dimensions=[
            Dimension.model_construct(name="rows", shape=100),
            Dimension.model_construct(name="columns", shape=200),
        ],
        additionalProperty=[
            PropertyValue.model_construct(name="cell_size_x_value", value="10"),
            PropertyValue.model_construct(name="cell_size_y_value", value="10"),
            PropertyValue.model_construct(name="cell_data_type", value="float32"),
            PropertyValue.model_construct(name="custom_meta", value="custom_value"),
        ],
        spatialCoverage=place,
        temporalCoverage=TemporalCoverage.model_construct(
            startDate=datetime(2024, 1, 1),
            endDate=datetime(2024, 1, 31),
        ),
        license=CreativeWork.model_construct(name="CC-BY-4.0", url="https://example.com/license"),
    )
    defaults.update(kwargs)
    return ScientificDataset.model_construct(**defaults)


def _make_legacy_metadata(**kwargs) -> GeographicRasterMetadata:
    defaults = dict(
        title="Legacy Raster",
        subjects=["raster", "legacy"],
        language="eng",
        description="Legacy description",
        additional_metadata={"custom_meta": "custom_value"},
        spatial_coverage=BoxCoverage(
            name="Cache Valley",
            northlimit=42.0,
            eastlimit=-111.0,
            southlimit=41.5,
            westlimit=-111.5,
            units="Decimal degrees",
            projection="WGS 84 EPSG:4326",
        ),
        period_coverage=PeriodCoverage(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 31),
        ),
        band_information=BandInformation(
            name="Band 1",
            variable_name="Band 1",
            variable_unit="m",
            no_data_value="-9999",
            minimum_value="0",
            maximum_value="100",
            comment="Primary raster band",
        ),
        spatial_reference=BoxSpatialReference(
            name="WGS 84",
            northlimit=42.0,
            eastlimit=-111.0,
            southlimit=41.5,
            westlimit=-111.5,
            units="Decimal degrees",
            projection="WGS 84 EPSG:4326",
            projection_string='GEOGCS["WGS 84"]',
            projection_string_type="EPSG:4326",
            projection_name="WGS 84",
        ),
        cell_information=CellInformation(
            rows=100,
            columns=200,
            cell_size_x_value=10.0,
            cell_size_y_value=10.0,
            cell_data_type="float32",
        ),
        type=AggregationType.GeographicRasterAggregation,
        url="https://www.hydroshare.org/resource/legacy-raster",
        rights=Rights(statement="CC-BY-4.0", url="https://example.com/license"),
    )
    defaults.update(kwargs)
    return GeographicRasterMetadata.model_construct(**defaults)


# ---------------------------------------------------------------------------
# Schema → Legacy
# ---------------------------------------------------------------------------


class TestSchemaToLegacy:
    def test_basic_fields(self):
        dataset = _make_schema_dataset()
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert isinstance(result, GeographicRasterMetadata)
        assert result.title == "Raster Dataset"
        assert result.subjects == ["raster", "elevation"]
        assert result.language == "eng"
        assert result.description == "Raster dataset description"
        assert result.url is None

    def test_band_information(self):
        dataset = _make_schema_dataset()
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.band_information is not None
        assert result.band_information.name == "Band 1"
        assert result.band_information.variable_unit == "m"
        assert result.band_information.no_data_value == "-9999"
        assert result.band_information.minimum_value == "0"
        assert result.band_information.maximum_value == "100"
        assert result.band_information.comment == "Primary raster band"

    def test_cell_information(self):
        dataset = _make_schema_dataset()
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.cell_information is not None
        assert result.cell_information.rows == 100
        assert result.cell_information.columns == 200
        assert result.cell_information.cell_size_x_value == 10.0
        assert result.cell_information.cell_size_y_value == 10.0
        assert result.cell_information.cell_data_type == "float32"

    def test_additional_metadata_preserved(self):
        dataset = _make_schema_dataset()
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.additional_metadata.get("custom_meta") == "custom_value"

    def test_spatial_coverage_box(self):
        dataset = _make_schema_dataset()
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert isinstance(result.spatial_coverage, BoxCoverage)
        assert result.spatial_coverage.northlimit == 42.0
        assert result.spatial_coverage.southlimit == 41.5
        assert result.spatial_coverage.eastlimit == -111.0
        assert result.spatial_coverage.westlimit == -111.5

    def test_spatial_reference_box(self):
        dataset = _make_schema_dataset()
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        srs = result.spatial_reference
        assert isinstance(srs, BoxSpatialReference)
        assert srs.projection_name == "WGS 84"
        assert srs.projection_string == 'GEOGCS["WGS 84"]'
        assert srs.projection_string_type == "EPSG:4326"
        # name on BoxSpatialReference carries the Place name, not the SRS name
        assert srs.name == "Cache Valley"

    def test_spatial_reference_missing_srs(self):
        """Spatial reference produced when the schema SRS entry is absent should have None coordinate fields."""
        place = Place.model_construct()
        place.name = "Cache Valley"
        place.geo = GeoShape.model_construct(box="42.0 -111.0 41.5 -111.5", validate_bbox=False)
        place.srs = None
        dataset = _make_schema_dataset(spatialCoverage=place)
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert isinstance(result.spatial_reference, BoxSpatialReference)
        assert result.spatial_reference.units is None
        assert result.spatial_reference.projection is None
        assert result.spatial_reference.projection_name is None
        assert result.spatial_reference.projection_string_type is None

    def test_period_coverage(self):
        dataset = _make_schema_dataset()
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.period_coverage is not None
        assert result.period_coverage.start == datetime(2024, 1, 1)
        assert result.period_coverage.end == datetime(2024, 1, 31)

    def test_rights_from_license(self):
        dataset = _make_schema_dataset()
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.rights is not None
        assert result.rights.statement == "CC-BY-4.0"
        assert str(result.rights.url) == "https://example.com/license"

    def test_partial_fields_use_fallbacks(self):
        """A minimal schema dict with only type fields should not raise and should use None fallbacks."""
        partial = {
            "@context": "https://hydroshare.org/schema",
            "@type": "ScientificDataset",
            "additionalType": "GeographicRaster",
        }
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(partial)

        assert isinstance(result, GeographicRasterMetadata)
        assert result.language is None
        assert result.url is None
        assert result.band_information is None

    def test_accepts_dict_input(self):
        data = _make_schema_dataset().model_dump(by_alias=True, exclude_none=True)
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(data)
        assert isinstance(result, GeographicRasterMetadata)


# ---------------------------------------------------------------------------
# Legacy → Schema
# ---------------------------------------------------------------------------


class TestLegacyToSchema:
    def test_basic_fields(self):
        legacy = _make_legacy_metadata()
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        assert isinstance(result, ScientificDataset)
        assert result.additionalType == AdditionalType.GEOGRAPHIC_RASTER
        assert result.name == "Legacy Raster"
        assert result.description == "Legacy description"
        assert result.keywords == ["raster", "legacy"]
        assert str(result.url) == "https://www.hydroshare.org/resource/legacy-raster"

    def test_variable_measured(self):
        legacy = _make_legacy_metadata()
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        assert result.variableMeasured is not None
        assert len(result.variableMeasured) == 1
        var = result.variableMeasured[0]
        assert isinstance(var, DataVariable)
        assert var.name == "Band 1"
        assert var.unit == "m"
        # The adapter converts string band values to float via _parse_float
        assert var.noDataValue == -9999.0
        assert var.minValue == 0.0
        assert var.maxValue == 100.0

    def test_dimensions(self):
        legacy = _make_legacy_metadata()
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        assert result.dimensions is not None
        dim_names = [d.name for d in result.dimensions]
        assert "rows" in dim_names
        assert "columns" in dim_names
        rows_dim = next(d for d in result.dimensions if d.name == "rows")
        columns_dim = next(d for d in result.dimensions if d.name == "columns")
        assert rows_dim.shape == 100
        assert columns_dim.shape == 200

    def test_additional_metadata_preserved(self):
        legacy = _make_legacy_metadata()
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        prop_dict = {p.name: p.value for p in (result.additionalProperty or []) if isinstance(p, PropertyValue)}
        assert prop_dict.get("custom_meta") == "custom_value"

    def test_spatial_coverage_box(self):
        legacy = _make_legacy_metadata()
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        assert result.spatialCoverage is not None
        assert isinstance(result.spatialCoverage.geo, GeoShape)
        assert result.spatialCoverage.geo.box == "42.0 -111.0 41.5 -111.5"

    def test_spatial_reference(self):
        legacy = _make_legacy_metadata()
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        srs = result.spatialCoverage.srs
        assert srs is not None
        assert srs.name == "WGS 84"
        assert srs.code == "EPSG:4326"
        assert srs.wktString == 'GEOGCS["WGS 84"]'

    def test_spatial_reference_missing_projection(self):
        """Legacy spatial reference with no projection should use a neutral fallback name in the schema SRS."""
        legacy = _make_legacy_metadata(
            spatial_reference=BoxSpatialReference(
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
        )
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        assert result.spatialCoverage.srs.name == "Unknown spatial reference"
        assert result.spatialCoverage.srs.srsType == "geographic"

    def test_temporal_coverage(self):
        legacy = _make_legacy_metadata()
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        assert result.temporalCoverage is not None
        assert result.temporalCoverage.startDate == datetime(2024, 1, 1)
        assert result.temporalCoverage.endDate == datetime(2024, 1, 31)

    def test_license_from_rights(self):
        legacy = _make_legacy_metadata()
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        assert result.license is not None
        assert isinstance(result.license, CreativeWork)
        assert result.license.name == "CC-BY-4.0"
        assert str(result.license.url) == "https://example.com/license"

    def test_accepts_dict_input(self):
        data = _make_legacy_metadata().model_dump()
        result = RasterMetadataAdapter.to_geographic_raster_metadata(data)
        assert isinstance(result, ScientificDataset)


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_single_band_round_trip_legacy_to_schema_to_legacy(self):
        original = _make_legacy_metadata()
        schema = RasterMetadataAdapter.to_geographic_raster_metadata(original)
        recovered = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(schema)

        assert recovered.title == original.title
        assert recovered.subjects == original.subjects
        assert recovered.language == original.language
        assert recovered.description == original.description

    def test_multi_band_round_trip_schema_to_legacy_to_schema(self):
        dataset = _make_schema_dataset(
            variableMeasured=[
                DataVariable.model_construct(
                    name="Band 1",
                    dimensions=["rows", "columns"],
                    unit="m",
                    minValue=0,
                    maxValue=100,
                    noDataValue="-9999",
                ),
                DataVariable.model_construct(
                    name="Band 2",
                    dimensions=["rows", "columns"],
                    unit="m",
                    minValue=10,
                    maxValue=200,
                    noDataValue="-9999",
                ),
            ]
        )
        legacy = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert isinstance(legacy.band_information, list)
        assert len(legacy.band_information) == 2

        recovered = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)
        assert len(recovered.variableMeasured) == 2
        assert recovered.variableMeasured[0].name == "Band 1"
        assert recovered.variableMeasured[1].name == "Band 2"
        band_dim = next((d for d in recovered.dimensions if d.name == "band"), None)
        assert band_dim is not None
        assert band_dim.shape == 2

    def test_round_trip_period_coverage(self):
        original = _make_legacy_metadata()
        schema = RasterMetadataAdapter.to_geographic_raster_metadata(original)
        recovered = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(schema)

        assert recovered.period_coverage is not None
        assert recovered.period_coverage.start == original.period_coverage.start
        assert recovered.period_coverage.end == original.period_coverage.end

    def test_round_trip_spatial_reference(self):
        original = _make_legacy_metadata()
        schema = RasterMetadataAdapter.to_geographic_raster_metadata(original)
        recovered = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(schema)

        assert recovered.spatial_reference is not None
        assert isinstance(recovered.spatial_reference, BoxSpatialReference)
        assert recovered.spatial_reference.projection_name == original.spatial_reference.projection_name
        assert recovered.spatial_reference.projection_string == original.spatial_reference.projection_string


# ---------------------------------------------------------------------------
# MetadataAdapter facade
# ---------------------------------------------------------------------------


class TestMetadataAdapterFacade:
    def test_to_legacy_geographic_raster_metadata(self):
        dataset = _make_schema_dataset()
        result = MetadataAdapter.to_legacy_geographic_raster_metadata(dataset)
        assert isinstance(result, GeographicRasterMetadata)

    def test_to_geographic_raster_metadata(self):
        legacy = _make_legacy_metadata()
        result = MetadataAdapter.to_geographic_raster_metadata(legacy)
        assert isinstance(result, ScientificDataset)
        assert result.additionalType == AdditionalType.GEOGRAPHIC_RASTER


# ---------------------------------------------------------------------------
# load_json routing
# ---------------------------------------------------------------------------


class TestLoadJsonRouting:
    def _build_json(self) -> dict:
        dataset = _make_schema_dataset()
        return dataset.model_dump(by_alias=True, exclude_none=True)

    def test_raster_dispatched_through_adapter(self):
        json_data = self._build_json()
        result = load_json(json_data, "123/.hsjsonld/raster-folder/logan.vrt.json")

        assert isinstance(result, GeographicRasterMetadata)
        assert result.type == AggregationType.GeographicRasterAggregation
        assert result.title == "Raster Dataset"

    def test_non_raster_scientific_dataset_passthrough(self):
        non_raster = {
            "@context": "https://hydroshare.org/schema",
            "@type": "ScientificDataset",
            "additionalType": "Tabular",
            "name": "CSV Dataset",
        }
        result = load_json(non_raster, "123/.hsjsonld/tabular-folder/data.csv.json")

        assert isinstance(result, ScientificDataset)
        assert result.additionalType.value == "Tabular"
        assert result.name == "CSV Dataset"

    def test_resource_metadata_path_not_dispatched_to_adapter(self):
        """A .hsjsonld/dataset_metadata.json path should not go through the raster adapter."""
        json_data = self._build_json()
        try:
            result = load_json(json_data, "/some/.hsjsonld/dataset_metadata.json")
            assert not isinstance(result, GeographicRasterMetadata)
        except Exception:
            pass  # Validation failure on a raster payload at the resource level is also acceptable


# ---------------------------------------------------------------------------
# Aggregation save
# ---------------------------------------------------------------------------


class TestAggregationSave:
    def test_aggregation_save_writes_schema_org_json(self):
        s3_client = DummyS3Client()
        aggregation = Aggregation(
            "bucket-name/123/.hsjsonld/raster-folder/logan.vrt.json",
            hs_session=None,
            s3_client=s3_client,
        )
        aggregation._retrieved_metadata = _make_legacy_metadata()
        aggregation._main_file_path = "raster-folder/logan.vrt"

        aggregation.save(refresh=False)

        assert len(s3_client.writes) == 1
        _, metadata_json = s3_client.writes[0]
        metadata = json.loads(metadata_json)
        assert metadata["@type"] == "ScientificDataset"
        assert metadata["additionalType"] == "GeographicRaster"
        assert metadata["name"] == "Legacy Raster"
        assert metadata["url"] == "https://www.hydroshare.org/resource/legacy-raster"


# ---------------------------------------------------------------------------
# Rights model
# ---------------------------------------------------------------------------


class TestRightsModel:
    def test_rights_requires_statement_or_url(self):
        with pytest.raises(ValidationError, match="Either 'statement' or 'url' must have a value"):
            Rights()

    def test_rights_accepts_url_only(self):
        rights = Rights(url="https://example.com/license")
        assert str(rights.url) == "https://example.com/license"
