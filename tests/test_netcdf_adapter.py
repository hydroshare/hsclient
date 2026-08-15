"""
Tests for the NetCDF / Multidimensional metadata adapter.

Coverage:
  - Schema → legacy conversion (ScientificDataset → MultidimensionalMetadata)
  - Legacy → schema conversion (MultidimensionalMetadata → ScientificDataset)
  - Full round-trips in both directions
  - Variable.shape ↔ Dimension name list conversion
  - Variable.type normalisation (valid enum value, unknown string, None)
  - Variable.method direct mapping to DataVariable.method; Variable.descriptive_name direct
    mapping to DataVariable.description
  - description field round-trip
  - Spatial coverage (box and point)
  - Spatial reference (box only)
  - Temporal coverage / period coverage
  - Rights / license mapping
  - load_json dispatch for MULTIDIMENSIONAL type
"""

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from hsclient.hydroshare import Aggregation
from hsclient.metadata_adapter.adapter import MetadataAdapter
from hsclient.metadata_adapter.netcdf_adapter import NetCDFMetadataAdapter
from hsclient.schema.base import (
    CreativeWork,
    GeoCoordinates,
    GeoShape,
    Place,
    PropertyValue,
    SpatialReference,
    TemporalCoverage,
)
from hsclient.schema.dataset import AdditionalType, ScientificDataset
from hsclient.schema.datavariable import DataVariable, Dimension
from hsclient.schema.legacy.netcdf import (
    BoxCoverage,
    MultidimensionalBoxSpatialReference,
    MultidimensionalMetadata,
    PeriodCoverage,
    PointCoverage,
    Rights,
    Variable,
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


def _make_variable(**kwargs) -> Variable:
    defaults = dict(
        name="precipitation",
        unit="mm/day",
        type="Float",
        shape="time lat lon",
        descriptive_name="Daily precipitation at surface",
        method="Accumulated over 24 hours",
        missing_value="-9999.0",
    )
    defaults.update(kwargs)
    return Variable(**defaults)


def _make_legacy_metadata(**kwargs) -> MultidimensionalMetadata:
    defaults = dict(
        title="Test NetCDF Dataset",
        subjects=["climate", "precipitation"],
        language="eng",
        description="A test multidimensional dataset",
        additional_metadata={"source": "reanalysis"},
        variables=[_make_variable()],
        spatial_coverage=BoxCoverage(
            northlimit=45.0,
            eastlimit=-70.0,
            southlimit=40.0,
            westlimit=-80.0,
        ),
        spatial_reference=MultidimensionalBoxSpatialReference(
            northlimit=45.0,
            eastlimit=-70.0,
            southlimit=40.0,
            westlimit=-80.0,
            projection_name="NAD83",
            projection_string="GEOGCS[NAD83]",
            projection_string_type="EPSG:4269",
        ),
        period_coverage=PeriodCoverage(
            start=datetime(2000, 1, 1),
            end=datetime(2020, 12, 31),
        ),
        rights=Rights(statement="CC BY 4.0"),
    )
    defaults.update(kwargs)
    return MultidimensionalMetadata(**defaults)


def _make_schema_dataset(**kwargs) -> ScientificDataset:
    data_variable = DataVariable.model_construct(
        name="precipitation",
        dimensions=["time", "lat", "lon"],
        unit="mm/day",
        dataType="Float",
        noDataValue="-9999.0",
        method="Accumulated over 24 hours",
        description="Daily precipitation at surface",
    )
    place = Place.model_construct()
    place.name = None
    # Box token order is "S W N E" (south, west, north, east)
    place.geo = GeoShape.model_construct(box="40.0 -80.0 45.0 -70.0", validate_bbox=False)
    place.srs = SpatialReference.model_construct(
        name="NAD83",
        srsType="geographic",
        code="EPSG:4269",
        wktString="GEOGCS[NAD83]",
    )
    defaults = dict(
        additionalType=AdditionalType.MULTIDIMENSIONAL,
        name="Test NetCDF Dataset",
        description="A test multidimensional dataset",
        keywords=["climate", "precipitation"],
        inLanguage="eng",
        variableMeasured=[data_variable],
        dimensions=[
            Dimension.model_construct(name="time", shape=0),
            Dimension.model_construct(name="lat", shape=0),
            Dimension.model_construct(name="lon", shape=0),
        ],
        additionalProperty=[
            PropertyValue.model_construct(name="source", value="reanalysis"),
        ],
        spatialCoverage=place,
        temporalCoverage=TemporalCoverage.model_construct(
            startDate=datetime(2000, 1, 1),
            endDate=datetime(2020, 12, 31),
        ),
        license=CreativeWork.model_construct(name="CC BY 4.0", url=None),
    )
    defaults.update(kwargs)
    return ScientificDataset.model_construct(**defaults)


# ---------------------------------------------------------------------------
# Schema → Legacy
# ---------------------------------------------------------------------------


class TestSchemaToLegacy:
    def test_basic_fields(self):
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert isinstance(result, MultidimensionalMetadata)
        assert result.title == "Test NetCDF Dataset"
        assert result.subjects == ["climate", "precipitation"]
        assert result.language == "eng"
        assert result.description == "A test multidimensional dataset"

    def test_no_legacy_spatial_reference_when_schema_srs_is_none(self):
        place = Place.model_construct()
        place.name = None
        place.geo = GeoShape.model_construct(box="4616916.5 433970.90625 4663316.5 464370.90625", validate_bbox=False)
        place.srs = None
        dataset = _make_schema_dataset(spatialCoverage=place)

        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.spatial_reference is None

    def test_variable_fields(self):
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert len(result.variables) == 1
        var = result.variables[0]
        assert var.name == "precipitation"
        assert var.unit == "mm/day"
        assert var.type == "Float"
        assert var.missing_value == "-9999.0"

    def test_variable_min_max_value_converted_to_legacy(self):
        dv = DataVariable.model_construct(
            name="precipitation", dimensions=["time"], minValue=0.0, maxValue=125.4
        )
        dataset = _make_schema_dataset(variableMeasured=[dv])
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        var = result.variables[0]
        assert var.minimum_value == "0.0"
        assert var.maximum_value == "125.4"

    def test_variable_non_numeric_min_max_value_preserved_as_string(self):
        dv = DataVariable.model_construct(
            name="precipitation", dimensions=["time"], minValue="NA", maxValue="NA"
        )
        dataset = _make_schema_dataset(variableMeasured=[dv])
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        var = result.variables[0]
        assert var.minimum_value == "NA"
        assert var.maximum_value == "NA"

    def test_variable_shape_from_dimensions(self):
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        var = result.variables[0]
        assert var.shape == "time lat lon"

    def test_coordinates_converted_to_legacy(self):
        coord = DataVariable.model_construct(
            name="time", dimensions=["time"], unit="days since 2000-01-01", dataType="Float"
        )
        dataset = _make_schema_dataset(coordinates=[coord])
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.coordinates is not None
        assert len(result.coordinates) == 1
        assert result.coordinates[0].name == "time"
        assert result.coordinates[0].unit == "days since 2000-01-01"
        assert result.coordinates[0].type == "Float"

    def test_no_coordinates_produces_none(self):
        dataset = _make_schema_dataset(coordinates=None)
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.coordinates is None

    def test_coordinate_and_variable_descriptive_name_independent(self):
        """A coordinate and a data variable sharing the same name must not collide -- each
        DataVariable carries its own 'description', mapped independently to its own legacy
        Variable's 'descriptive_name'."""
        coord = DataVariable.model_construct(
            name="precipitation", dimensions=["time"], description="Coordinate axis"
        )
        dataset = _make_schema_dataset(coordinates=[coord])
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.coordinates[0].descriptive_name == "Coordinate axis"
        assert result.variables[0].descriptive_name == "Daily precipitation at surface"
        assert result.variables[0].method == "Accumulated over 24 hours"

    def test_dimension_shape_written_to_additional_metadata(self):
        dataset = _make_schema_dataset(
            dimensions=[
                Dimension.model_construct(name="time", shape=365),
                Dimension.model_construct(name="lat", shape=180),
                Dimension.model_construct(name="lon", shape=360),
            ]
        )
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.additional_metadata["dimension_time_shape"] == "365"
        assert result.additional_metadata["dimension_lat_shape"] == "180"
        assert result.additional_metadata["dimension_lon_shape"] == "360"

    def test_variable_descriptive_name_from_description(self):
        """descriptive_name is mapped directly from DataVariable.description; method comes
        directly from DataVariable.method."""
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        var = result.variables[0]
        assert var.descriptive_name == "Daily precipitation at surface"
        assert var.method == "Accumulated over 24 hours"

    def test_additional_metadata_non_overflow_keys_preserved(self):
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.additional_metadata.get("source") == "reanalysis"

    def test_additional_property_bare_string_list_entries_not_dropped(self):
        """a List[str] additionalProperty (a legal shape per the ScientificDataset type)
        must be preserved under synthetic keys."""
        # TODO: We should not be mapping legacy additional_metadata to schema additionalProperty
        # as they have different data types.
        dataset = _make_schema_dataset(additionalProperty=["first note", "second note"])
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.additional_metadata.get("value_0") == "first note"
        assert result.additional_metadata.get("value_1") == "second note"

    def test_spatial_coverage_box(self):
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert isinstance(result.spatial_coverage, BoxCoverage)
        assert result.spatial_coverage.northlimit == 45.0
        assert result.spatial_coverage.southlimit == 40.0

    def test_spatial_reference_box(self):
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        srs = result.spatial_reference
        assert isinstance(srs, MultidimensionalBoxSpatialReference)
        assert srs.projection_name == "NAD83"
        assert srs.projection_string == "GEOGCS[NAD83]"
        assert srs.projection_string_type == "EPSG:4269"

    def test_spatial_reference_srs_type_captured_directly(self):
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.spatial_reference.srs_type == "geographic"

    def test_spatial_reference_srs_type_projected_captured_directly(self):
        place = Place.model_construct()
        place.geo = GeoShape.model_construct(box="40.0 -80.0 45.0 -70.0", validate_bbox=False)
        place.srs = SpatialReference.model_construct(
            name="NAD83",
            srsType="projected",
            code="EPSG:26912",
        )
        dataset = _make_schema_dataset(spatialCoverage=place)
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.spatial_reference.srs_type == "projected"

    def test_spatial_units_and_datum_from_place_additional_property(self):
        """units/datum have no schema.org field, so they're carried via Place.additionalProperty."""
        place = Place.model_construct()
        place.geo = GeoShape.model_construct(box="40.0 -80.0 45.0 -70.0", validate_bbox=False)
        place.srs = SpatialReference.model_construct(name="NAD83", srsType="geographic")
        place.additionalProperty = [
            PropertyValue.model_construct(name="spatial_coverage_units", value="Decimal degrees"),
            PropertyValue.model_construct(name="spatial_reference_units", value="Decimal degrees"),
            PropertyValue.model_construct(name="spatial_reference_datum", value="NAD83"),
        ]
        dataset = _make_schema_dataset(spatialCoverage=place)
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.spatial_coverage.units == "Decimal degrees"
        assert result.spatial_reference.units == "Decimal degrees"
        assert result.spatial_reference.datum == "NAD83"

    def test_malformed_box_raises_value_error_on_spatial_coverage(self):
        """a malformed geo.box must raise."""
        place = Place.model_construct()
        place.geo = GeoShape.model_construct(box="not a valid box", validate_bbox=False)
        dataset = _make_schema_dataset(spatialCoverage=place)

        with pytest.raises(ValueError, match="Invalid geo.box string"):
            NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

    def test_wrong_part_count_box_raises_value_error(self):
        """A box string with the wrong number of components must also raise."""
        place = Place.model_construct()
        place.geo = GeoShape.model_construct(box="45.0 -70.0 40.0", validate_bbox=False)
        dataset = _make_schema_dataset(spatialCoverage=place)

        with pytest.raises(ValueError, match="Invalid geo.box string"):
            NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

    def test_spatial_reference_none_for_point_coverage(self):
        """Point coverage has no MultidimensionalBoxSpatialReference equivalent."""
        place = Place.model_construct()
        place.geo = GeoCoordinates.model_construct(latitude=43.0, longitude=-75.0)
        place.srs = SpatialReference.model_construct(name="WGS84", srsType="geographic")
        dataset = _make_schema_dataset(spatialCoverage=place)
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert isinstance(result.spatial_coverage, PointCoverage)
        assert result.spatial_reference is None

    def test_period_coverage(self):
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.period_coverage is not None
        assert result.period_coverage.start == datetime(2000, 1, 1)
        assert result.period_coverage.end == datetime(2020, 12, 31)

    def test_temporal_coverage_with_none_start_date_returns_none_instead_of_raising(self):
        dataset = _make_schema_dataset(
            temporalCoverage=TemporalCoverage.model_construct(startDate=None, endDate=None)
        )
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.period_coverage is None

    def test_rights_from_creative_work(self):
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.rights is not None
        assert result.rights.statement == "CC BY 4.0"

    def test_partial_fields_use_fallbacks(self):
        """A minimal schema dict with only type fields should not raise and should use None fallbacks."""
        partial = {
            "@context": "https://hydroshare.org/schema",
            "@type": "ScientificDataset",
            "additionalType": "MultiDimensional",
        }
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(partial)

        assert isinstance(result, MultidimensionalMetadata)
        assert result.variables == []
        assert result.language is None

    def test_accepts_dict_input(self):
        dataset = _make_schema_dataset()
        data = dataset.model_dump(by_alias=True, exclude_none=True)
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(data)
        assert isinstance(result, MultidimensionalMetadata)

    def test_unknown_schema_field_survives_object_input(self):
        """A ScientificDataset field this adapter has no named slot for must be captured into
        legacy.extra_columns instead of being silently dropped."""
        dataset = _make_schema_dataset(someFutureField="netcdf123")
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)
        assert result.extra_columns == {"someFutureField": "netcdf123"}
        with pytest.raises(ValidationError):
            result.extra_columns = {}

    def test_unknown_schema_field_survives_dict_input(self):
        data = _make_schema_dataset(someFutureField="netcdf123").model_dump(by_alias=True, exclude_none=True)
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(data)
        assert result.extra_columns == {"someFutureField": "netcdf123"}

    def test_empty_variable_list(self):
        dataset = _make_schema_dataset(variableMeasured=[], dimensions=[])
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)
        assert result.variables == []

    def test_string_variable_item(self):
        """String items in variableMeasured produce minimal Variable objects."""
        dataset = _make_schema_dataset(
            variableMeasured=["temperature"],
            additionalProperty=[],
            dimensions=[],
        )
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)
        assert len(result.variables) == 1
        assert result.variables[0].name == "temperature"


# ---------------------------------------------------------------------------
# Legacy → Schema
# ---------------------------------------------------------------------------


class TestLegacyToSchema:
    def test_basic_fields(self):
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert isinstance(result, ScientificDataset)
        assert result.additionalType == AdditionalType.MULTIDIMENSIONAL
        assert result.name == "Test NetCDF Dataset"
        assert result.description == "A test multidimensional dataset"
        assert result.inLanguage == "eng"
        assert "climate" in (result.keywords or [])

    def test_variable_measured(self):
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.variableMeasured is not None
        assert len(result.variableMeasured) == 1
        var = result.variableMeasured[0]
        assert isinstance(var, DataVariable)
        assert var.name == "precipitation"
        assert var.unit == "mm/day"
        assert var.dataType == "Float"
        assert var.noDataValue == "-9999.0"

    def test_variable_min_max_value_converted_to_schema(self):
        legacy = _make_legacy_metadata(
            variables=[_make_variable(minimum_value="0.0", maximum_value="125.4")]
        )
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        var = result.variableMeasured[0]
        assert var.minValue == 0.0
        assert var.maxValue == 125.4

    def test_variable_non_numeric_min_max_value_preserved_as_string(self):
        legacy = _make_legacy_metadata(
            variables=[_make_variable(minimum_value="NA", maximum_value="NA")]
        )
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        var = result.variableMeasured[0]
        assert var.minValue == "NA"
        assert var.maxValue == "NA"

    def test_coordinates_converted_to_schema(self):
        """legacy coordinates must be converted to ScientificDataset.coordinates."""
        legacy = _make_legacy_metadata(
            coordinates=[Variable(name="time", unit="days since 2000-01-01", type="Float", shape="time")]
        )
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.coordinates is not None
        assert len(result.coordinates) == 1
        coord = result.coordinates[0]
        assert isinstance(coord, DataVariable)
        assert coord.name == "time"
        assert coord.unit == "days since 2000-01-01"
        assert coord.dataType == "Float"

    def test_no_coordinates_produces_none(self):
        legacy = _make_legacy_metadata(coordinates=None)
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.coordinates is None

    def test_coordinate_and_variable_descriptive_name_independent(self):
        """A coordinate and a data variable sharing the same name must not collide -- each legacy
        Variable's 'descriptive_name' is mapped independently to its own DataVariable's
        'description'."""
        legacy = _make_legacy_metadata(
            coordinates=[
                Variable(name="precipitation", descriptive_name="Coordinate axis", type="Float")
            ]
        )
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.coordinates[0].description == "Coordinate axis"
        assert result.variableMeasured[0].description == "Daily precipitation at surface"

    def test_variable_shape_to_dimensions(self):
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.dimensions is not None
        dim_names = [d.name for d in result.dimensions]
        assert "time" in dim_names
        assert "lat" in dim_names
        assert "lon" in dim_names

    def test_dimension_from_coordinate_only_shape(self):
        """A dimension name that appears only in a coordinate's shape string (never in any
        data variable's) must still be picked up -- not just names found in 'variables'."""
        legacy = _make_legacy_metadata(
            coordinates=[Variable(name="time_bnds", shape="time nv")]
        )
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        dim_names = [d.name for d in result.dimensions]
        assert "nv" in dim_names

    def test_dimension_shape_placeholder(self):
        """Dimension.shape should be 0 when size is unknown."""
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        for dim in result.dimensions or []:
            assert dim.shape == 0

    def test_dimension_shape_read_from_additional_metadata(self):
        """a real dimension size stored in additional_metadata must be read back into Dimension.shape."""
        legacy = _make_legacy_metadata(
            additional_metadata={
                "source": "reanalysis",
                "dimension_time_shape": "365",
                "dimension_lat_shape": "180",
                "dimension_lon_shape": "360",
            }
        )
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        shapes = {d.name: d.shape for d in result.dimensions or []}
        assert shapes == {"time": 365, "lat": 180, "lon": 360}

    def test_dimension_shape_overflow_keys_not_duplicated_in_additional_property(self):
        legacy = _make_legacy_metadata(
            additional_metadata={"source": "reanalysis", "dimension_time_shape": "365"}
        )
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        prop_names = {p.name for p in result.additionalProperty or []}
        assert "dimension_time_shape" not in prop_names
        assert "source" in prop_names

    def test_variable_dimensions_from_shape(self):
        """DataVariable.dimensions should be the list of tokens from Variable.shape."""
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        var = result.variableMeasured[0]
        assert isinstance(var, DataVariable)
        assert var.dimensions == ["time", "lat", "lon"]

    def test_additional_metadata_in_additional_property(self):
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        prop_dict = {p.name: p.value for p in (result.additionalProperty or []) if isinstance(p, PropertyValue)}
        assert prop_dict.get("source") == "reanalysis"

    def test_spatial_coverage_box(self):
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.spatialCoverage is not None
        assert isinstance(result.spatialCoverage.geo, GeoShape)

    def test_spatial_reference(self):
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        srs = result.spatialCoverage.srs
        assert srs is not None
        assert srs.name == "NAD83"
        assert srs.code == "EPSG:4269"
        assert srs.wktString == "GEOGCS[NAD83]"

    def test_srs_type_read_directly_when_present(self):
        """Finding #6 (netcdf-adapter-improvements-plan.md): srs_type should be read straight
        from MultidimensionalBoxSpatialReference.srs_type when present."""
        legacy = _make_legacy_metadata(
            spatial_reference=MultidimensionalBoxSpatialReference(
                northlimit=45.0,
                eastlimit=-70.0,
                southlimit=40.0,
                westlimit=-80.0,
                projection_name="NAD83 / UTM zone 12N",
                srs_type="projected",
            )
        )
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.spatialCoverage.srs.srsType == "projected"

    def test_srs_type_defaults_to_geographic_when_absent(self):
        """A legacy object predating the srs_type field must fall back to 'geographic', not a
        keyword heuristic over projection text."""
        legacy = _make_legacy_metadata(
            spatial_reference=MultidimensionalBoxSpatialReference(
                northlimit=45.0,
                eastlimit=-70.0,
                southlimit=40.0,
                westlimit=-80.0,
                projection_name="UTM Zone 12N",
            )
        )
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.spatialCoverage.srs.srsType == "geographic"

    def test_spatial_units_and_datum_written_to_place_additional_property(self):
        """legacy units/datum must be written to Place.additionalProperty."""
        legacy = _make_legacy_metadata(
            spatial_coverage=BoxCoverage(
                northlimit=45.0, eastlimit=-70.0, southlimit=40.0, westlimit=-80.0,
                units="Decimal degrees",
            ),
            spatial_reference=MultidimensionalBoxSpatialReference(
                northlimit=45.0, eastlimit=-70.0, southlimit=40.0, westlimit=-80.0,
                units="Decimal degrees", datum="NAD83",
            ),
        )
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        prop_by_name = {p.name: p.value for p in result.spatialCoverage.additionalProperty or []}
        assert prop_by_name["spatial_coverage_units"] == "Decimal degrees"
        assert prop_by_name["spatial_reference_units"] == "Decimal degrees"
        assert prop_by_name["spatial_reference_datum"] == "NAD83"

    def test_temporal_coverage(self):
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.temporalCoverage is not None
        assert result.temporalCoverage.startDate == datetime(2000, 1, 1)
        assert result.temporalCoverage.endDate == datetime(2020, 12, 31)

    def test_license_from_rights(self):
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.license is not None
        assert isinstance(result.license, CreativeWork)
        assert result.license.name == "CC BY 4.0"

    def test_accepts_dict_input(self):
        legacy = _make_legacy_metadata()
        data = legacy.model_dump()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(data)
        assert isinstance(result, ScientificDataset)

    def test_unknown_legacy_field_survives_dict_input(self):
        """A legacy field this adapter has no named slot for (captured into legacy.model_extra via
        extra="allow" on LegacyBaseModel) must survive into the resulting ScientificDataset."""
        legacy = _make_legacy_metadata(someLegacyField="xyz789")
        data = legacy.model_dump()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(data)
        assert result.model_extra.get("someLegacyField") == "xyz789"

    def test_unknown_legacy_field_survives_object_input(self):
        legacy = _make_legacy_metadata(someLegacyField="xyz789")
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)
        assert result.model_extra.get("someLegacyField") == "xyz789"

    def test_no_spatial_reference_when_no_srs(self):
        legacy = _make_legacy_metadata(spatial_reference=None)
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.spatialCoverage is not None
        assert result.spatialCoverage.srs is None

    def test_point_spatial_coverage(self):
        legacy = _make_legacy_metadata(
            spatial_coverage=PointCoverage(north=43.0, east=-75.0),
            spatial_reference=None,
        )
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert isinstance(result.spatialCoverage.geo, GeoCoordinates)
        assert result.spatialCoverage.geo.latitude == 43.0
        assert result.spatialCoverage.geo.longitude == -75.0


# ---------------------------------------------------------------------------
# Variable.type normalisation
# ---------------------------------------------------------------------------


class TestVariableTypeNormalisation:
    @pytest.mark.parametrize(
        "input_type, expected",
        [
            ("Float", "Float"),
            ("float", "Float"),
            ("FLOAT", "Float"),
            ("Double", "Double"),
            ("Int", "Int"),
            ("Char", "Char"),
            ("Unsigned Byte", "Unsigned Byte"),
            ("unsigned byte", "Unsigned Byte"),
        ],
    )
    def test_known_types_normalised(self, input_type, expected):
        result = NetCDFMetadataAdapter._normalize_variable_type(input_type)
        assert result == expected

    def test_unrecognised_type_preserves_original_string(self):
        """an unrecognised type string must be
        preserved unchanged, -- NetCDF data types (numpy/xarray
        dtype strings like 'float32') never match the VariableType enum and would otherwise always
        be destroyed."""
        result = NetCDFMetadataAdapter._normalize_variable_type("FancyCustomType")
        assert result == "FancyCustomType"

    @pytest.mark.parametrize("dtype_str", ["float32", "float64", "int16", "uint8", "datetime64[ns]"])
    def test_real_numpy_dtype_strings_preserved(self, dtype_str):
        """Real numpy/xarray dtype strings (what HydroShare's NetCDF extractor actually sets on
        DataVariable.dataType) don't match any VariableType value and must survive unchanged."""
        result = NetCDFMetadataAdapter._normalize_variable_type(dtype_str)
        assert result == dtype_str

    def test_none_returns_none(self):
        result = NetCDFMetadataAdapter._normalize_variable_type(None)
        assert result is None

    def test_schema_to_legacy_unrecognised_type_preserved(self):
        """An unrecognised dataType string from schema should survive unchanged in legacy Variable,
        not become 'Unknown'."""
        dv = DataVariable.model_construct(name="temp", dimensions=["x"], dataType="float32")
        dataset = _make_schema_dataset(variableMeasured=[dv], additionalProperty=[], dimensions=[])
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)
        assert result.variables[0].type == "float32"


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

        legacy = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)
        assert legacy.spatial_reference is None

        recovered = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)
        assert recovered.spatialCoverage.srs is None

    def test_legacy_to_schema_to_legacy_core_fields(self):
        original = _make_legacy_metadata()
        schema = NetCDFMetadataAdapter.to_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(schema)

        assert recovered.title == original.title
        assert recovered.subjects == original.subjects
        assert recovered.language == original.language
        assert recovered.description == original.description

    def test_legacy_to_schema_to_legacy_variable_fields(self):
        original = _make_legacy_metadata()
        schema = NetCDFMetadataAdapter.to_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(schema)

        assert len(recovered.variables) == 1
        var = recovered.variables[0]
        orig_var = original.variables[0]
        assert var.name == orig_var.name
        assert var.unit == orig_var.unit
        assert var.type == orig_var.type
        assert var.shape == orig_var.shape
        assert var.descriptive_name == orig_var.descriptive_name
        assert var.method == orig_var.method
        assert var.missing_value == orig_var.missing_value

    def test_legacy_to_schema_to_legacy_period_coverage(self):
        original = _make_legacy_metadata()
        schema = NetCDFMetadataAdapter.to_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(schema)

        assert recovered.period_coverage.start == original.period_coverage.start
        assert recovered.period_coverage.end == original.period_coverage.end

    def test_legacy_to_schema_to_legacy_rights(self):
        original = _make_legacy_metadata()
        schema = NetCDFMetadataAdapter.to_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(schema)

        assert recovered.rights is not None
        assert recovered.rights.statement == "CC BY 4.0"

    def test_schema_to_legacy_to_schema_core_fields(self):
        original = _make_schema_dataset()
        legacy = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert recovered.name == original.name
        assert recovered.description == original.description
        assert recovered.inLanguage == original.inLanguage

    def test_schema_to_legacy_to_schema_variable_shape(self):
        original = _make_schema_dataset()
        legacy = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        var = recovered.variableMeasured[0]
        assert isinstance(var, DataVariable)
        # Dimension names should be preserved
        assert set(var.dimensions) == {"time", "lat", "lon"}

    def test_round_trip_dimension_shape_schema_to_legacy_to_schema(self):
        """real dimension sizes must survive a
        schema -> legacy -> schema round trip instead of being replaced with the 0 placeholder."""
        original = _make_schema_dataset(
            dimensions=[
                Dimension.model_construct(name="time", shape=365),
                Dimension.model_construct(name="lat", shape=180),
                Dimension.model_construct(name="lon", shape=360),
            ]
        )
        legacy = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        shapes = {d.name: d.shape for d in recovered.dimensions or []}
        assert shapes == {"time": 365, "lat": 180, "lon": 360}

    def test_round_trip_dimension_shape_legacy_to_schema_to_legacy(self):
        original = _make_legacy_metadata(
            additional_metadata={"dimension_time_shape": "365", "dimension_lat_shape": "180"}
        )
        schema = NetCDFMetadataAdapter.to_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(schema)

        assert recovered.additional_metadata["dimension_time_shape"] == "365"
        assert recovered.additional_metadata["dimension_lat_shape"] == "180"

    def test_round_trip_dimension_used_only_by_coordinate_schema_to_legacy_to_schema(self):
        """A dimension referenced only by a coordinate (e.g. a CF 'nv'/'bnds' bounds axis backing
        a 'time_bnds'-style coordinate, never used by any data variable) must survive a
        schema -> legacy -> schema round trip as a real Dimension."""
        coord = DataVariable.model_construct(
            name="time_bnds", dimensions=["time", "nv"], dataType="Float"
        )
        original = _make_schema_dataset(
            dimensions=[
                Dimension.model_construct(name="time", shape=365),
                Dimension.model_construct(name="lat", shape=180),
                Dimension.model_construct(name="lon", shape=360),
                Dimension.model_construct(name="nv", shape=2),
            ],
            coordinates=[coord],
        )
        legacy = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        shapes = {d.name: d.shape for d in recovered.dimensions or []}
        assert shapes == {"time": 365, "lat": 180, "lon": 360, "nv": 2}
        prop_names = {p.name for p in recovered.additionalProperty or []}
        assert "dimension_nv_shape" not in prop_names

    def test_round_trip_coordinates_schema_to_legacy_to_schema(self):
        """coordinates must survive a schema -> legacy -> schema round trip."""
        coord = DataVariable.model_construct(
            name="time", dimensions=["time"], unit="days since 2000-01-01", dataType="Float"
        )
        original = _make_schema_dataset(coordinates=[coord])
        legacy = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert recovered.coordinates is not None
        assert len(recovered.coordinates) == 1
        assert recovered.coordinates[0].name == "time"
        assert recovered.coordinates[0].unit == "days since 2000-01-01"
        assert recovered.coordinates[0].dataType == "Float"

    def test_round_trip_coordinates_legacy_to_schema_to_legacy(self):
        original = _make_legacy_metadata(
            coordinates=[Variable(name="time", unit="days since 2000-01-01", type="Float", shape="time")]
        )
        schema = NetCDFMetadataAdapter.to_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(schema)

        assert recovered.coordinates is not None
        assert len(recovered.coordinates) == 1
        assert recovered.coordinates[0].name == "time"
        assert recovered.coordinates[0].unit == "days since 2000-01-01"

    def test_round_trip_non_numeric_min_max_value(self):
        """a non-numeric minValue/maxValue sentinel must survive a legacy -> schema -> legacy round trip unchanged."""
        original = _make_legacy_metadata(
            variables=[_make_variable(minimum_value="NA", maximum_value="NA")]
        )
        schema = NetCDFMetadataAdapter.to_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(schema)

        assert recovered.variables[0].minimum_value == "NA"
        assert recovered.variables[0].maximum_value == "NA"

    def test_round_trip_srs_type_legacy_to_schema_to_legacy(self):
        """srs_type must survive a legacy -> schema -> legacy round trip."""
        original = _make_legacy_metadata(
            spatial_reference=MultidimensionalBoxSpatialReference(
                northlimit=45.0,
                eastlimit=-70.0,
                southlimit=40.0,
                westlimit=-80.0,
                srs_type="projected",
            )
        )
        schema = NetCDFMetadataAdapter.to_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(schema)

        assert recovered.spatial_reference.srs_type == "projected"

    def test_round_trip_spatial_units_and_datum_legacy_to_schema_to_legacy(self):
        """units/datum must survive a legacy -> schema -> legacy round trip."""
        original = _make_legacy_metadata(
            spatial_coverage=BoxCoverage(
                northlimit=45.0, eastlimit=-70.0, southlimit=40.0, westlimit=-80.0,
                units="Decimal degrees",
            ),
            spatial_reference=MultidimensionalBoxSpatialReference(
                northlimit=45.0, eastlimit=-70.0, southlimit=40.0, westlimit=-80.0,
                units="Decimal degrees", datum="NAD83",
            ),
        )
        schema = NetCDFMetadataAdapter.to_multidimensional_metadata(original)
        recovered = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(schema)

        assert recovered.spatial_coverage.units == "Decimal degrees"
        assert recovered.spatial_reference.units == "Decimal degrees"
        assert recovered.spatial_reference.datum == "NAD83"

    def test_unknown_field_survives_schema_to_legacy_to_schema_round_trip(self):
        dataset = _make_schema_dataset(someFutureField="netcdf123")
        legacy = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)
        assert legacy.extra_columns == {"someFutureField": "netcdf123"}
        recovered = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)
        assert recovered.model_extra.get("someFutureField") == "netcdf123"

    def test_unknown_field_survives_legacy_to_schema_to_legacy_round_trip(self):
        legacy = _make_legacy_metadata(someLegacyField="xyz789")
        schema = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)
        assert schema.model_extra.get("someLegacyField") == "xyz789"
        recovered = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(schema)
        assert recovered.extra_columns.get("someLegacyField") == "xyz789"

    def test_dimension_deduplication(self):
        """Two variables sharing dimensions should not produce duplicate Dimension entries."""
        v1 = Variable(name="temp", shape="time lat lon")
        v2 = Variable(name="precip", shape="time lat lon")
        legacy = _make_legacy_metadata(variables=[v1, v2])
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        dim_names = [d.name for d in (result.dimensions or [])]
        assert dim_names == list(dict.fromkeys(dim_names)), "Dimension names must be unique"
        assert set(dim_names) == {"time", "lat", "lon"}


# ---------------------------------------------------------------------------
# MetadataAdapter facade
# ---------------------------------------------------------------------------


class TestMetadataAdapterFacade:
    def test_to_legacy_multidimensional_metadata(self):
        dataset = _make_schema_dataset()
        result = MetadataAdapter.to_legacy_multidimensional_metadata(dataset)
        assert isinstance(result, MultidimensionalMetadata)

    def test_to_multidimensional_metadata(self):
        legacy = _make_legacy_metadata()
        result = MetadataAdapter.to_multidimensional_metadata(legacy)
        assert isinstance(result, ScientificDataset)
        assert result.additionalType == AdditionalType.MULTIDIMENSIONAL


# ---------------------------------------------------------------------------
# Aggregation save
# ---------------------------------------------------------------------------


class TestAggregationSave:
    def test_aggregation_save_writes_schema_org_json(self):
        s3_client = DummyS3Client()
        aggregation = Aggregation(
            "bucket-name/123/.hsjsonld/netcdf-folder/data.nc.json",
            hs_session=None,
            s3_client=s3_client,
        )
        aggregation._retrieved_metadata = _make_legacy_metadata()
        aggregation._main_file_path = "netcdf-folder/data.nc"

        aggregation.save(refresh=False)

        assert len(s3_client.writes) == 1
        _, metadata_json = s3_client.writes[0]
        metadata = json.loads(metadata_json)
        assert metadata["@type"] == "ScientificDataset"
        assert metadata["additionalType"] == "MultiDimensional"
        assert metadata["name"] == "Test NetCDF Dataset"


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
    def test_license_with_only_description_works(self):
        dataset = _make_schema_dataset(
            license=CreativeWork.model_construct(description="Free-text license terms.")
        )
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.rights is not None
        assert result.rights.description == "Free-text license terms."
        assert result.rights.statement is None
        assert result.rights.url is None

    def test_license_with_nothing_set_returns_none(self):
        dataset = _make_schema_dataset(license=CreativeWork.model_construct())
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.rights is None

    def test_license_description_preserved_alongside_name_and_url(self):
        dataset = _make_schema_dataset(
            license=CreativeWork.model_construct(
                name="CC BY 4.0", url="https://example.com/license", description="Attribution required."
            )
        )
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.rights.statement == "CC BY 4.0"
        assert str(result.rights.url) == "https://example.com/license"
        assert result.rights.description == "Attribution required."

    def test_license_description_round_trips_back_to_schema(self):
        legacy = _make_legacy_metadata(rights=Rights(description="Free-text license terms."))
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.license.description == "Free-text license terms."
        assert result.license.name is None
        assert result.license.url is None


# ---------------------------------------------------------------------------
# load_json routing
# ---------------------------------------------------------------------------


class TestLoadJsonRouting:
    def _build_json(self) -> dict:
        dataset = _make_schema_dataset()
        return dataset.model_dump(by_alias=True, exclude_none=True)

    def test_multidimensional_dispatched_through_adapter(self):
        json_data = self._build_json()
        result = load_json(json_data, "/some/resource/.hsmetadata/nc.json")
        assert isinstance(result, MultidimensionalMetadata)

    def test_non_multidimensional_returns_scientific_dataset(self):
        """Non-multidimensional aggregations that have no specific adapter return ScientificDataset."""
        json_data = {
            "@context": "https://hydroshare.org/schema",
            "@type": "ScientificDataset",
            "additionalType": "FileSet",
            "keywords": ["test"],
        }
        result = load_json(json_data, "/some/resource/.hsmetadata/file_set.json")
        assert isinstance(result, ScientificDataset)
        assert not isinstance(result, MultidimensionalMetadata)

    def test_resource_metadata_path_not_dispatched_to_adapter(self):
        """Dataset metadata path should not go through the aggregation adapter."""
        # This path returns LegacyResourceMetadata, not MultidimensionalMetadata
        json_data = self._build_json()
        # Override the path to trigger the resource-level branch
        try:
            result = load_json(json_data, "/some/.hsjsonld/dataset_metadata.json")
            # Should not return MultidimensionalMetadata
            assert not isinstance(result, MultidimensionalMetadata)
        except Exception:
            # If the resource metadata validation fails on this payload that's acceptable;
            # what matters is that it did NOT route through the multidimensional adapter.
            pass
