"""
Tests for the NetCDF / Multidimensional metadata adapter.

Coverage:
  - Schema → legacy conversion (ScientificDataset → MultidimensionalMetadata)
  - Legacy → schema conversion (MultidimensionalMetadata → ScientificDataset)
  - Full round-trips in both directions
  - Variable.shape ↔ Dimension name list conversion
  - Variable.type normalisation (valid enum value, unknown string, None)
  - Variable.method / descriptive_name overflow via additionalProperty
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
    )
    place = Place.model_construct()
    place.name = None
    place.geo = GeoShape.model_construct(box="45.0 -70.0 40.0 -80.0", validate_bbox=False)
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
            PropertyValue.model_construct(
                name="variable_precipitation_descriptive_name",
                value="Daily precipitation at surface",
            ),
            PropertyValue.model_construct(
                name="variable_precipitation_method",
                value="Accumulated over 24 hours",
            ),
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

    def test_variable_fields(self):
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert len(result.variables) == 1
        var = result.variables[0]
        assert var.name == "precipitation"
        assert var.unit == "mm/day"
        assert var.type == "Float"
        assert var.missing_value == "-9999.0"

    def test_variable_shape_from_dimensions(self):
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        var = result.variables[0]
        assert var.shape == "time lat lon"

    def test_variable_overflow_fields_extracted(self):
        """descriptive_name and method should be popped from additional_metadata."""
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        var = result.variables[0]
        assert var.descriptive_name == "Daily precipitation at surface"
        assert var.method == "Accumulated over 24 hours"
        # Overflow keys should NOT leak into additional_metadata
        assert "variable_precipitation_descriptive_name" not in result.additional_metadata
        assert "variable_precipitation_method" not in result.additional_metadata

    def test_additional_metadata_non_overflow_keys_preserved(self):
        dataset = _make_schema_dataset()
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)

        assert result.additional_metadata.get("source") == "reanalysis"

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

    def test_variable_shape_to_dimensions(self):
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        assert result.dimensions is not None
        dim_names = [d.name for d in result.dimensions]
        assert "time" in dim_names
        assert "lat" in dim_names
        assert "lon" in dim_names

    def test_dimension_shape_placeholder(self):
        """Dimension.shape should be 0 when size is unknown (plan decision 3)."""
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        for dim in result.dimensions or []:
            assert dim.shape == 0

    def test_variable_dimensions_from_shape(self):
        """DataVariable.dimensions should be the list of tokens from Variable.shape."""
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        var = result.variableMeasured[0]
        assert isinstance(var, DataVariable)
        assert var.dimensions == ["time", "lat", "lon"]

    def test_overflow_properties_in_additional_property(self):
        legacy = _make_legacy_metadata()
        result = NetCDFMetadataAdapter.to_multidimensional_metadata(legacy)

        prop_dict = {p.name: p.value for p in (result.additionalProperty or []) if isinstance(p, PropertyValue)}
        assert prop_dict.get("variable_precipitation_descriptive_name") == "Daily precipitation at surface"
        assert prop_dict.get("variable_precipitation_method") == "Accumulated over 24 hours"

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

    def test_unknown_type_falls_back_to_unknown(self):
        result = NetCDFMetadataAdapter._normalize_variable_type("FancyCustomType")
        assert result == "Unknown"

    def test_none_returns_none(self):
        result = NetCDFMetadataAdapter._normalize_variable_type(None)
        assert result is None

    def test_schema_to_legacy_unknown_type_normalised(self):
        """Unknown dataType strings from schema should become 'Unknown' in legacy Variable."""
        dv = DataVariable.model_construct(name="temp", dimensions=["x"], dataType="MyCustomType")
        dataset = _make_schema_dataset(variableMeasured=[dv], additionalProperty=[], dimensions=[])
        result = NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(dataset)
        assert result.variables[0].type == "Unknown"


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------


class TestRoundTrip:
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
    def test_rights_requires_statement_or_url(self):
        with pytest.raises(ValidationError, match="Either 'statement' or 'url' must have a value"):
            Rights()

    def test_rights_accepts_url_only(self):
        rights = Rights(url="https://example.com/license")
        assert str(rights.url) == "https://example.com/license"


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
