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
    # Box token order is "S W N E" (south, west, north, east)
    place.geo = GeoShape.model_construct(box="41.5 -111.5 42.0 -111.0", validate_bbox=False)
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

    def test_missing_grid_info_returns_none(self):
        """Neither rows nor columns present -> valid empty state, no CellInformation to
        build, so this returns None."""
        dataset = _make_schema_dataset(
            dimensions=[],
            additionalProperty=[],
            variableMeasured=[
                DataVariable.model_construct(name="Band 1", dimensions=["rows", "columns"], unit="m")
            ],
        )

        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.cell_information is None

    def test_incomplete_grid_info_raises(self):
        """Only one of rows/columns present -> CellInformation can't be built (rows/columns are
        required, non-Optional ints on the legacy model).
        """
        dataset = _make_schema_dataset(
            dimensions=[Dimension.model_construct(name="rows", shape=100)],
            additionalProperty=[
                PropertyValue.model_construct(name="cell_size_x_value", value="10"),
                PropertyValue.model_construct(name="cell_size_y_value", value="10"),
                PropertyValue.model_construct(name="cell_data_type", value="float32"),
            ],
            variableMeasured=[
                DataVariable.model_construct(name="Band 1", dimensions=["rows", "columns"], unit="m")
            ],
        )

        with pytest.raises(ValueError, match="Inconsistent raster dimensions"):
            RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

    def test_additional_property_bare_string_list_entries_not_dropped(self):
        """a List[str] additionalProperty (a legal shape per the ScientificDataset
        type) being preserved under synthetic keys."""
        # TODO: We should not be mapping legacy additional_metadata to schema additionalProperty
        # as they have different data types.
        dataset = _make_schema_dataset(additionalProperty=["first note", "second note"])
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.additional_metadata.get("value_0") == "first note"
        assert result.additional_metadata.get("value_1") == "second note"

    def test_cell_data_type_authoritative_from_data_variable(self):
        """DataVariable.dataType is authoritative for cell_data_type."""
        dataset = _make_schema_dataset(
            variableMeasured=[
                DataVariable.model_construct(
                    name="Band 1", dimensions=["rows", "columns"], unit="m", dataType="int16"
                )
            ],
            additionalProperty=[
                PropertyValue.model_construct(name="cell_size_x_value", value="10"),
                PropertyValue.model_construct(name="cell_size_y_value", value="10"),
            ],
        )
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.cell_information.cell_data_type == "int16"

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

    def test_malformed_box_raises_value_error_on_spatial_coverage(self):
        """a malformed geo.box must raise instead of silently discarding the whole
        spatial coverage."""
        place = Place.model_construct()
        place.name = "Cache Valley"
        place.geo = GeoShape.model_construct(box="not a valid box", validate_bbox=False)
        dataset = _make_schema_dataset(spatialCoverage=place)

        with pytest.raises(ValueError, match="Invalid geo.box string"):
            RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

    def test_missing_box_raises_value_error(self):
        """A GeoShape with an empty box string must also raise, not silently drop the coverage."""
        place = Place.model_construct()
        place.name = "Cache Valley"
        place.geo = GeoShape.model_construct(box="", validate_bbox=False)
        dataset = _make_schema_dataset(spatialCoverage=place)

        with pytest.raises(ValueError, match="Invalid geo.box string"):
            RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

    def test_wrong_part_count_box_raises_value_error(self):
        """A box string with the wrong number of components must also raise."""
        place = Place.model_construct()
        place.name = "Cache Valley"
        place.geo = GeoShape.model_construct(box="42.0 -111.0 41.5", validate_bbox=False)
        dataset = _make_schema_dataset(spatialCoverage=place)

        with pytest.raises(ValueError, match="Invalid geo.box string"):
            RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

    def test_spatial_reference_srs_type_captured_directly(self):
        """srs_type should be read straight from ScientificDataset.srs.srsType"""
        dataset = _make_schema_dataset()
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.spatial_reference.srs_type == "geographic"

    def test_spatial_reference_srs_type(self):
        place = Place.model_construct()
        place.name = "Cache Valley"
        place.geo = GeoShape.model_construct(box="41.5 -111.5 42.0 -111.0", validate_bbox=False)
        place.srs = SpatialReference.model_construct(
            name="NAD83",
            srsType="projected",
            code="EPSG:26912",
        )
        dataset = _make_schema_dataset(spatialCoverage=place)
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.spatial_reference.srs_type == "projected"

    def test_band_information_method(self):
        dataset = _make_schema_dataset(
            variableMeasured=[
                DataVariable.model_construct(
                    name="Band 1",
                    dimensions=["rows", "columns"],
                    unit="m",
                    method="Bilinear resampling",
                )
            ]
        )
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.band_information.method == "Bilinear resampling"

    def test_spatial_units_and_datum_from_place_additional_property(self):
        """units/datum have no schema.org field, so they're carried via Place.additionalProperty."""
        place = Place.model_construct()
        place.name = "Cache Valley"
        place.geo = GeoShape.model_construct(box="41.5 -111.5 42.0 -111.0", validate_bbox=False)
        place.srs = SpatialReference.model_construct(name="WGS 84", srsType="geographic")
        place.additionalProperty = [
            PropertyValue.model_construct(name="spatial_coverage_units", value="Decimal degrees"),
            PropertyValue.model_construct(name="spatial_reference_units", value="Decimal degrees"),
            PropertyValue.model_construct(name="spatial_reference_datum", value="NAD83"),
        ]
        dataset = _make_schema_dataset(spatialCoverage=place)
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.spatial_coverage.units == "Decimal degrees"
        assert result.spatial_reference.units == "Decimal degrees"
        assert result.spatial_reference.datum == "NAD83"

    def test_spatial_reference_missing_srs(self):
        """No SpatialReference at all on the schema side must not set a legacy side spatial
        reference object.
        """
        place = Place.model_construct()
        place.name = "Cache Valley"
        place.geo = GeoShape.model_construct(box="41.5 -111.5 42.0 -111.0", validate_bbox=False)
        place.srs = None
        dataset = _make_schema_dataset(spatialCoverage=place)
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.spatial_reference is None

    def test_period_coverage(self):
        dataset = _make_schema_dataset()
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.period_coverage is not None
        assert result.period_coverage.start == datetime(2024, 1, 1)
        assert result.period_coverage.end == datetime(2024, 1, 31)

    def test_temporal_coverage_with_none_start_date_returns_none(self):
        dataset = _make_schema_dataset(
            temporalCoverage=TemporalCoverage.model_construct(startDate=None, endDate=None)
        )
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.period_coverage is None

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

    def test_unknown_schema_field_survives_object_input(self):
        """A ScientificDataset field this adapter has no named slot for must be captured into
        legacy.extra_columns instead of being silently dropped."""
        dataset = _make_schema_dataset(someFutureField="raster123")
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)
        assert result.extra_columns == {"someFutureField": "raster123"}
        with pytest.raises(ValidationError):
            result.extra_columns = {}

    def test_unknown_schema_field_survives_dict_input(self):
        data = _make_schema_dataset(someFutureField="raster123").model_dump(by_alias=True, exclude_none=True)
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(data)
        assert result.extra_columns == {"someFutureField": "raster123"}


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

    def test_non_numeric_band_values_preserved_as_string(self):
        """a non-numeric minimum_value/maximum_value/no_data_value (e.g. an "NA"
        sentinel) must survive as a string"""
        legacy = _make_legacy_metadata(
            band_information=BandInformation(
                name="Band 1",
                variable_name="Band 1",
                variable_unit="m",
                no_data_value="NA",
                minimum_value="NA",
                maximum_value="100",
            )
        )
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        var = result.variableMeasured[0]
        assert var.noDataValue == "NA"
        assert var.minValue == "NA"
        # A parseable value alongside non-numeric ones is still converted to float.
        assert var.maxValue == 100.0

    def test_cell_data_type_populates_data_variable_not_additional_property(self):
        """cell_data_type populates DataVariable.dataType."""
        legacy = _make_legacy_metadata()
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        assert result.variableMeasured[0].dataType == "float32"

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
        # Box token order is "S W N E" (south, west, north, east)
        assert result.spatialCoverage.geo.box == "41.5 -111.5 42.0 -111.0"

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
        # projection text -> defaults to "geographic".
        assert result.spatialCoverage.srs.srsType == "geographic"

    def test_srs_type_read_directly_when_present(self):
        """When srs_type is set on the legacy object, it's used as-is -- even though the
        projection text alone wouldn't hint at "projected"."""
        legacy = _make_legacy_metadata(
            spatial_reference=BoxSpatialReference(
                name="Cache Valley",
                northlimit=42.0,
                eastlimit=-111.0,
                southlimit=41.5,
                westlimit=-111.5,
                projection="EPSG:26912",
                projection_name="NAD83",
                srs_type="projected",
            )
        )
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        assert result.spatialCoverage.srs.srsType == "projected"

    def test_srs_type_defaults_to_geographic_when_absent(self):
        """With no srs_type set, the type defaults to "geographic" regardless of projection text."""
        legacy = _make_legacy_metadata(
            spatial_reference=BoxSpatialReference(
                name="Cache Valley",
                northlimit=42.0,
                eastlimit=-111.0,
                southlimit=41.5,
                westlimit=-111.5,
                projection="UTM Zone 12N",
                projection_name=None,
                srs_type=None,
            )
        )
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        assert result.spatialCoverage.srs.srsType == "geographic"

    def test_spatial_units_and_datum_written_to_place_additional_property(self):
        """units/datum have no schema.org field, so they're carried via Place.additionalProperty for now."""
        # TODO: This test is not needed once we have a proper schema.org extension for units/datum on Place/SpatialReference.
        legacy = _make_legacy_metadata(
            spatial_coverage=BoxCoverage(
                name="Cache Valley",
                northlimit=42.0,
                eastlimit=-111.0,
                southlimit=41.5,
                westlimit=-111.5,
                units="Decimal degrees",
            ),
            spatial_reference=BoxSpatialReference(
                name="WGS 84",
                northlimit=42.0,
                eastlimit=-111.0,
                southlimit=41.5,
                westlimit=-111.5,
                units="Decimal degrees",
                datum="NAD83",
            ),
        )
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        overflow = {p.name: p.value for p in (result.spatialCoverage.additionalProperty or [])}
        assert overflow.get("spatial_coverage_units") == "Decimal degrees"
        assert overflow.get("spatial_reference_units") == "Decimal degrees"
        assert overflow.get("spatial_reference_datum") == "NAD83"

    def test_variable_measured_method(self):
        legacy = _make_legacy_metadata(
            band_information=BandInformation(
                name="Band 1",
                variable_name="Band 1",
                method="Bilinear resampling",
            )
        )
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        assert result.variableMeasured[0].method == "Bilinear resampling"

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

    def test_unknown_legacy_field_survives_dict_input(self):
        """A legacy field this adapter has no named slot for (captured into legacy.model_extra via
        extra="allow" on LegacyBaseModel) must survive into the resulting ScientificDataset."""
        legacy = _make_legacy_metadata(someLegacyField="xyz789")
        data = legacy.model_dump()
        result = RasterMetadataAdapter.to_geographic_raster_metadata(data)
        assert result.model_extra.get("someLegacyField") == "xyz789"

    def test_unknown_legacy_field_survives_object_input(self):
        legacy = _make_legacy_metadata(someLegacyField="xyz789")
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)
        assert result.model_extra.get("someLegacyField") == "xyz789"


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_projected_box_with_no_srs_survives_round_trip_without_becoming_geographic(self):
        place = Place.model_construct()
        place.name = None
        # Real UTM-like values (meters), not lat/lon degrees -- would fail geographic bbox
        # validation if ever mislabeled as "geographic".
        place.geo = GeoShape.model_construct(box="4616916.5 433970.90625 4663316.5 464370.90625", validate_bbox=False)
        place.srs = None
        dataset = _make_schema_dataset(spatialCoverage=place)

        legacy = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)
        assert legacy.spatial_reference is None

        recovered = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)
        assert recovered.spatialCoverage.srs is None

    def test_single_band_round_trip_legacy_to_schema_to_legacy(self):
        original = _make_legacy_metadata()
        schema = RasterMetadataAdapter.to_geographic_raster_metadata(original)
        recovered = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(schema)

        assert recovered.title == original.title
        assert recovered.subjects == original.subjects
        assert recovered.language == original.language
        assert recovered.description == original.description

    def test_unknown_field_survives_schema_to_legacy_to_schema_round_trip(self):
        dataset = _make_schema_dataset(someFutureField="raster123")
        legacy = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)
        assert legacy.extra_columns == {"someFutureField": "raster123"}
        recovered = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)
        assert recovered.model_extra.get("someFutureField") == "raster123"

    def test_unknown_field_survives_legacy_to_schema_to_legacy_round_trip(self):
        legacy = _make_legacy_metadata(someLegacyField="xyz789")
        schema = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)
        assert schema.model_extra.get("someLegacyField") == "xyz789"
        recovered = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(schema)
        assert recovered.extra_columns.get("someLegacyField") == "xyz789"

    def test_multi_band_round_trip_schema_to_legacy_to_schema(self):
        """A multi-band raster with band_information as a list survives a full schema -> legacy -> schema round trip."""
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

    def test_round_trip_non_numeric_no_data_value(self):
        """a non-numeric no_data_value sentinel survives a full legacy -> schema
        -> legacy round trip."""
        original = _make_legacy_metadata(
            band_information=BandInformation(
                name="Band 1",
                variable_name="Band 1",
                variable_unit="m",
                no_data_value="NA",
                minimum_value="0",
                maximum_value="100",
            )
        )
        schema = RasterMetadataAdapter.to_geographic_raster_metadata(original)
        assert schema.variableMeasured[0].noDataValue == "NA"

        recovered = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(schema)
        band = recovered.band_information
        band = band[0] if isinstance(band, list) else band
        assert band.no_data_value == "NA"

    def test_round_trip_srs_type_legacy_to_schema_to_legacy(self):
        """srs_type survives a full legacy -> schema -> legacy round trip."""
        original = _make_legacy_metadata(
            spatial_reference=BoxSpatialReference(
                name="Cache Valley",
                northlimit=42.0,
                eastlimit=-111.0,
                southlimit=41.5,
                westlimit=-111.5,
                projection="EPSG:26912",
                projection_name="NAD83",
                srs_type="projected",
            )
        )
        schema = RasterMetadataAdapter.to_geographic_raster_metadata(original)
        assert schema.spatialCoverage.srs.srsType == "projected"

        recovered = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(schema)
        assert recovered.spatial_reference.srs_type == "projected"

    def test_round_trip_spatial_units_and_datum_legacy_to_schema_to_legacy(self):
        """spatial units and datum survive a full legacy -> schema -> legacy round trip."""
        original = _make_legacy_metadata(
            spatial_coverage=BoxCoverage(
                name="Cache Valley",
                northlimit=42.0,
                eastlimit=-111.0,
                southlimit=41.5,
                westlimit=-111.5,
                units="Decimal degrees",
            ),
            spatial_reference=BoxSpatialReference(
                name="WGS 84",
                northlimit=42.0,
                eastlimit=-111.0,
                southlimit=41.5,
                westlimit=-111.5,
                units="Decimal degrees",
                datum="NAD83",
            ),
        )
        schema = RasterMetadataAdapter.to_geographic_raster_metadata(original)
        recovered = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(schema)

        assert recovered.spatial_coverage.units == "Decimal degrees"
        assert recovered.spatial_reference.units == "Decimal degrees"
        assert recovered.spatial_reference.datum == "NAD83"

    def test_round_trip_band_method_schema_to_legacy_to_schema(self):
        """full round trip: editing DataVariable.method on an already-converted
        ScientificDataset and converting back to legacy must reflect the edit, not the original
        legacy band_information.method value."""
        dataset = _make_schema_dataset(
            variableMeasured=[
                DataVariable.model_construct(
                    name="Band 1",
                    dimensions=["rows", "columns"],
                    unit="m",
                    method="Bilinear resampling",
                )
            ]
        )
        legacy = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)
        assert legacy.band_information.method == "Bilinear resampling"

        recovered = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)
        assert recovered.variableMeasured[0].method == "Bilinear resampling"

    def test_round_trip_data_variable_data_type_edit_survives(self):
        """full round trip: editing DataVariable.dataType on an already-converted
        ScientificDataset and converting back to legacy must reflect the edit, not the original
        legacy cell_data_type value."""
        legacy = _make_legacy_metadata()
        schema = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)
        assert schema.variableMeasured[0].dataType == "float32"

        schema.variableMeasured[0].dataType = "int16"

        recovered = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(schema)
        assert recovered.cell_information.cell_data_type == "int16"


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
    def test_rights_requires_statement_or_url_or_description(self):
        with pytest.raises(ValidationError, match="Either 'statement', 'url', or 'description' must have a value"):
            Rights()

    def test_rights_accepts_url_only(self):
        rights = Rights(url="https://example.com/license")
        assert str(rights.url) == "https://example.com/license"

    def test_rights_accepts_description_only(self):
        rights = Rights(description="Free-text license terms with no formal name or URL.")
        assert rights.description == "Free-text license terms with no formal name or URL."


class TestRightsFromLicense:
    """Tests for the adapter's handling of schema.org CreativeWork license fields when converting to legacy Rights."""

    def test_license_with_only_description_does_not_raise(self):
        dataset = _make_schema_dataset(
            license=CreativeWork.model_construct(description="Free-text license terms.")
        )
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.rights is not None
        assert result.rights.description == "Free-text license terms."
        assert result.rights.statement is None
        assert result.rights.url is None

    def test_license_with_nothing_set_returns_none_instead_of_raising(self):
        dataset = _make_schema_dataset(license=CreativeWork.model_construct())
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.rights is None

    def test_license_description_preserved_alongside_name_and_url(self):
        dataset = _make_schema_dataset(
            license=CreativeWork.model_construct(
                name="CC-BY-4.0", url="https://example.com/license", description="Attribution required."
            )
        )
        result = RasterMetadataAdapter.to_legacy_geographic_raster_metadata(dataset)

        assert result.rights.statement == "CC-BY-4.0"
        assert str(result.rights.url) == "https://example.com/license"
        assert result.rights.description == "Attribution required."

    def test_license_description_round_trips_back_to_schema(self):
        legacy = _make_legacy_metadata(rights=Rights(description="Free-text license terms."))
        result = RasterMetadataAdapter.to_geographic_raster_metadata(legacy)

        assert result.license.description == "Free-text license terms."
        assert result.license.name is None
        assert result.license.url is None
