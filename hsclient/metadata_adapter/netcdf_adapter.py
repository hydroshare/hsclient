from __future__ import annotations

"""
Adapter between the locally-owned MultidimensionalMetadata legacy model and the
schema.org-based ScientificDataset.

Conversion directions
---------------------
  to_legacy_multidimensional_metadata : ScientificDataset | dict → MultidimensionalMetadata
  to_multidimensional_metadata        : MultidimensionalMetadata | dict → ScientificDataset

Variable.descriptive_name <-> DataVariable.description
--------------------------------------------------------

Variable.method <-> DataVariable.method
NOTE: 'method' field has been added locally to DataVariable (note DataVariable is not a schema-org term)

Coordinates
-----------
'ScientificDataset.coordinates' (coordinate axis variables, e.g. lat/lon/time -- distinct from
'variableMeasured', the actual data variables) has no equivalent on
'hsmodels.schemas.aggregations.MultidimensionalMetadata'. 'MultidimensionalMetadata' gained an additive 'coordinates:
Optional[List[Variable]]' field to round-trip it.


Variable.shape ↔ Dimension mapping
------------------------------------
'Variable.shape' in the legacy model is a space-separated string of dimension names,
e.g. '"time lat lon"'.  'ScientificDataset' represents each dimension as a 'Dimension'
object with a 'name' (str) and a required 'shape' (size of the dimension as an int) -- and HydroShare's NetCDF
extractor populates that 'shape' with the dimension's actual axis length (e.g. 365 for a
365-step time axis).

The legacy model has no per-dimension size slot of its own -- only dimension names survive
directly via 'Variable.shape' -- so real sizes are round-tripped via 'additional_metadata'
under the keys:

  'dimension_{dimname}_shape'

NOTE: This is not a permanent solution; it is a temporary workaround to preserve dimension
sizes across the round-trip until a better mechanism is implemented.
TODO: Consider adding a proper per-dimension size field to the legacy model.


Variable.type
-------------
'Variable.type' in the legacy model corresponds to 'hsmodels.schemas.enums.VariableType', but is
stored here as a plain 'Optional[str]' (not a real 'VariableType'-constrained enum), since
HydroShare's extractor sets 'DataVariable.dataType' from the numpy/xarray dtype string (e.g.
'"float32"', '"int64"', '"datetime64[ns]"'), not an OPeNDAP/netCDF type name. The value is passed
through unchanged in both conversion directions.


SpatialReference.srsType ↔ MultidimensionalBoxSpatialReference.srs_type
-------------------------------------------------------------------------
'srs_type' is a dedicated field on 'MultidimensionalBoxSpatialReference' (added specifically for
this round trip, it has no equivalent in 'hsmodels'). It is populated directly from
'ScientificDataset.spatialCoverage.srs.srsType' on the schema → legacy leg, and read back directly
on the legacy → schema leg, defaulting to '"geographic"'.

Spatial units/datum overflow fields
------------------------------------
'BoxCoverage.units'/'PointCoverage.units' 
and 'MultidimensionalBoxSpatialReference.units'/'datum' already exist on the legacy models but
have no equivalent on 'GeoShape'/'GeoCoordinates'/'SpatialReference' -- this is a schema.org-side
gap. They are round-tripped via 'Place.additionalProperty':

  'spatial_coverage_units'
  'spatial_reference_units'
  'spatial_reference_datum'

NOTE: This is not a permanent solution; it is a temporary workaround to preserve these fields across the round-trip
until a better mechanism is implemented.
TODO: Consider adding these missing fields to schema side models.
"""

from typing import Any, Dict, List, Optional, Union

from hsmodels.schemas.enums import AggregationType

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

class NetCDFMetadataAdapter:
    """Translate Multidimensional (NetCDF) metadata between ScientificDataset and the
    locally-owned MultidimensionalMetadata legacy model."""

    _DEFAULT_SRS_NAME = "Unknown spatial reference"

    # ------------------------------------------------------------------
    # Public conversion methods
    # ------------------------------------------------------------------

    @classmethod
    def to_legacy_multidimensional_metadata(
        cls, metadata: Union[ScientificDataset, Dict[str, Any]]
    ) -> MultidimensionalMetadata:
        """Convert a ScientificDataset (or its dict representation) to MultidimensionalMetadata.
        """
        dataset = metadata if isinstance(metadata, ScientificDataset) else ScientificDataset.model_validate(metadata)

        # Start with the flat additionalProperty → dict conversion.
        additional_metadata = cls._additional_property_to_dict(dataset.additionalProperty)

        # Real dimension sizes have no per-dimension slot on the legacy model; preserve them via
        # additional_metadata overflow keys.
        cls._dimensions_to_overflow_metadata(dataset.dimensions, additional_metadata)

        variables = cls._schema_to_legacy_variables(dataset.variableMeasured)
        coordinates = cls._schema_to_legacy_variables(dataset.coordinates)

        return MultidimensionalMetadata(
            type=AggregationType.MultidimensionalAggregation,
            title=dataset.name,
            subjects=dataset.keywords or [],
            language=dataset.inLanguage,
            description=dataset.description,
            additional_metadata=additional_metadata,
            spatial_coverage=cls._to_legacy_spatial_coverage(dataset.spatialCoverage),
            period_coverage=cls._to_legacy_period_coverage(dataset.temporalCoverage),
            variables=variables,
            coordinates=coordinates or None,
            spatial_reference=cls._to_legacy_spatial_reference(dataset.spatialCoverage),
            url=dataset.url,
            rights=cls._to_legacy_rights(dataset.license),
            associatedMedia=dataset.associatedMedia,
            # Preserve any schema.org field this adapter doesn't declare a named field for so it survives
            # the round trip instead of being silently dropped.
            extra_columns=dict(dataset.model_extra or {}),
        )

    @classmethod
    def to_multidimensional_metadata(
        cls, metadata: Union[MultidimensionalMetadata, Dict[str, Any]]
    ) -> ScientificDataset:
        """Convert a MultidimensionalMetadata legacy metadata object (or dict) to a ScientificDataset."""
        if isinstance(metadata, MultidimensionalMetadata):
            legacy = metadata
        else:
            legacy = MultidimensionalMetadata.model_validate(metadata)

        additional_metadata = dict(legacy.additional_metadata or {})
        dimensions = cls._variable_shape_to_dimensions(legacy.variables, additional_metadata, legacy.coordinates)

        additional_properties = cls._dict_to_additional_property(additional_metadata)
        extras = dict(legacy.extra_columns or {})
        extras.update(legacy.model_extra or {})
        extras.update(
            additionalType=AdditionalType.MULTIDIMENSIONAL,
            name=legacy.title,
            description=legacy.description,
            inLanguage=legacy.language,
            keywords=legacy.subjects or [],
            license=cls._to_schema_license(legacy.rights),
            url=legacy.url,
            additionalProperty=additional_properties or None,
            spatialCoverage=cls._to_schema_spatial_coverage(
                legacy.spatial_coverage,
                legacy.spatial_reference,
            ),
            temporalCoverage=cls._to_schema_temporal_coverage(legacy.period_coverage),
            variableMeasured=cls._to_schema_variable_measured(legacy.variables),
            coordinates=cls._to_schema_variable_measured(legacy.coordinates or []) or None,
            dimensions=dimensions,
            associatedMedia=legacy.associatedMedia,
        )
        return ScientificDataset.model_construct(**extras)

    # ------------------------------------------------------------------
    # Variable conversion helpers
    # ------------------------------------------------------------------

    @classmethod
    def _schema_to_legacy_variables(
        cls,
        variable_measured: Optional[List[Union[str, PropertyValue, DataVariable]]],
    ) -> List[Variable]:
        """Convert a ScientificDataset variable list ('variableMeasured' or 'coordinates') to a
        list of legacy Variable objects.

        'descriptive_name' is read directly from 'DataVariable.description', and 'method'
        directly from 'DataVariable.method'
        """
        if not variable_measured:
            return []

        variables: List[Variable] = []
        for item in variable_measured:
            if isinstance(item, DataVariable):
                # Resolve shape: DataVariable.dimensions is Union[str, list[str]].
                dims = item.dimensions
                if isinstance(dims, list):
                    shape = " ".join(dims)
                else:
                    shape = dims or ""

                variables.append(
                    Variable(
                        name=item.name,
                        unit=item.unit,
                        type=item.dataType,
                        shape=shape,
                        descriptive_name=item.description,
                        method=item.method,
                        missing_value=cls._to_str(item.noDataValue),
                        minimum_value=cls._to_str(item.minValue),
                        maximum_value=cls._to_str(item.maxValue),
                    )
                )
            elif isinstance(item, PropertyValue):
                variables.append(Variable(name=item.name))
            elif isinstance(item, str):
                variables.append(Variable(name=item))

        return variables

    @staticmethod
    def _to_schema_variable_measured(variables: List[Variable]) -> List[DataVariable]:
        """Convert legacy Variable list → list of DataVariable objects.

        'Variable.descriptive_name' is mapped directly to 'DataVariable.description', and
        'Variable.method' directly to 'DataVariable.method'
        """
        result: List[DataVariable] = []
        for var in variables:
            dims = (var.shape or "").split() if var.shape else []
            result.append(
                DataVariable.model_construct(
                    name=var.name,
                    dimensions=dims,
                    unit=var.unit,
                    dataType=var.type,
                    noDataValue=var.missing_value,
                    minValue=NetCDFMetadataAdapter._parse_float_or_original(var.minimum_value),
                    maxValue=NetCDFMetadataAdapter._parse_float_or_original(var.maximum_value),
                    method=var.method,
                    description=var.descriptive_name,
                )
            )
        return result

    @staticmethod
    def _variable_shape_to_dimensions(
        variables: List[Variable],
        additional_metadata: Optional[Dict[str, str]] = None,
        coordinates: Optional[List[Variable]] = None,
    ) -> List[Dimension]:
        """Derive a deduplicated Dimension list from variable shape strings.
        """
        additional_metadata = additional_metadata if additional_metadata is not None else {}
        seen: Dict[str, bool] = {}
        for var in list(variables) + list(coordinates or []):
            for dim_name in (var.shape or "").split():
                if dim_name and dim_name not in seen:
                    seen[dim_name] = True

        dimensions: List[Dimension] = []
        for dim_name in seen:
            shape = NetCDFMetadataAdapter._parse_int(additional_metadata.pop(f"dimension_{dim_name}_shape", None))
            dimensions.append(Dimension.model_construct(name=dim_name, shape=shape if shape is not None else 0))
        return dimensions

    @staticmethod
    def _dimensions_to_overflow_metadata(
        dimensions: Optional[List[Dimension]], additional_metadata: Dict[str, str]
    ) -> None:
        """Write each Dimension's real integer shape into 'additional_metadata' (in place) under
        'dimension_{dimname}_shape' keys.

        The legacy MultidimensionalMetadata/Variable models have no per-dimension size slot --
        'Variable.shape' only records dimension names -- so real sizes from
        'ScientificDataset.dimensions' are round-tripped via this additional_metadata overflow
        instead.
        # TODO: Consider adding a proper per-dimension size field to the legacy model.
        """
        for dimension in dimensions or []:
            if not dimension.name:
                continue
            additional_metadata[f"dimension_{dimension.name}_shape"] = str(dimension.shape)

    # ------------------------------------------------------------------
    # Spatial coverage helpers
    # ------------------------------------------------------------------

    @classmethod
    def _to_legacy_spatial_coverage(
        cls, spatial_coverage: Optional[Place]
    ) -> Optional[Union[BoxCoverage, PointCoverage]]:
        """Convert ScientificDataset.spatialCoverage → legacy BoxCoverage or PointCoverage."""
        if spatial_coverage is None or spatial_coverage.geo is None:
            return None

        # NOTE: GeoShape/GeoCoordinates carry no 'units' concept in schema.org, unlike the
        # legacy BoxCoverage/PointCoverage models which do. This one field, 'units', is
        # round-tripped via Place.additionalProperty under the key "spatial_coverage_units".
        # TODO: Consider adding a proper 'units' field to GeoShape/GeoCoordinates/SpatialReference.
        overflow = cls._additional_property_to_dict(spatial_coverage.additionalProperty)
        units = overflow.get("spatial_coverage_units")

        geo = spatial_coverage.geo
        if isinstance(geo, GeoShape):
            north, east, south, west = cls._parse_bbox(geo.box)
            return BoxCoverage(
                type="box",
                name=spatial_coverage.name,
                northlimit=north,
                eastlimit=east,
                southlimit=south,
                westlimit=west,
                units=units,
                projection=None,
            )

        if isinstance(geo, GeoCoordinates):
            return PointCoverage(
                type="point",
                name=spatial_coverage.name,
                east=geo.longitude,
                north=geo.latitude,
                units=units,
                projection=None,
            )

        return None

    @classmethod
    def _to_legacy_spatial_reference(
        cls, spatial_coverage: Optional[Place]
    ) -> Optional[MultidimensionalBoxSpatialReference]:
        """Convert ScientificDataset.spatialCoverage.srs → MultidimensionalBoxSpatialReference.

        Multidimensional aggregations only support a box-type
        spatial reference.  If the spatial coverage geometry is a point (GeoCoordinates),
        this method returns None rather than creating an unsupported point reference.
        """
        if spatial_coverage is None or spatial_coverage.geo is None:
            return None

        geo = spatial_coverage.geo
        # Only box coverage maps to a box spatial reference.
        if not isinstance(geo, GeoShape):
            return None

        if spatial_coverage.srs is None:
            # No spatial reference on the schema side at all, means no spatial reference on the legacy side also
            return None

        north, east, south, west = cls._parse_bbox(geo.box)

        srs = spatial_coverage.srs
        projection_name = srs.name
        projection = srs.code or srs.name
        projection_string = srs.wktString
        projection_string_type = srs.code
        srs_type = srs.srsType

        # NOTE: 'units' and 'datum' have no schema.org equivalent -- SpatialReference (Place.srs)
        # carries neither, so -- same as 'spatial_coverage_units' above -- they're round-tripped
        # via Place.additionalProperty.
        # TODO: Consider adding proper 'units' and 'datum' fields to GeoShape/GeoCoordinates/SpatialReference.
        overflow = cls._additional_property_to_dict(spatial_coverage.additionalProperty)
        units = overflow.get("spatial_reference_units")
        datum = overflow.get("spatial_reference_datum")

        return MultidimensionalBoxSpatialReference(
            type="box",
            name=spatial_coverage.name,
            northlimit=north,
            eastlimit=east,
            southlimit=south,
            westlimit=west,
            units=units,
            projection=projection,
            projection_string=projection_string,
            projection_string_type=projection_string_type,
            projection_name=projection_name,
            srs_type=srs_type,
            datum=datum,
        )

    @classmethod
    def _to_schema_spatial_coverage(
        cls,
        spatial_coverage: Optional[Union[BoxCoverage, PointCoverage]],
        spatial_reference: Optional[MultidimensionalBoxSpatialReference],
    ) -> Optional[Place]:
        """Convert legacy spatial coverage + spatial reference → ScientificDataset.spatialCoverage."""
        if spatial_coverage is None:
            return None

        place = Place.model_construct()
        place.name = getattr(spatial_coverage, "name", None)

        if isinstance(spatial_coverage, BoxCoverage):
            # NOTE: Legacy BoxCoverage.units has no dedicated GeoShape field; preserved via
            # Place.additionalProperty below instead.
            place.geo = GeoShape.model_construct(
                box=cls._compose_box(
                    spatial_coverage.northlimit,
                    spatial_coverage.eastlimit,
                    spatial_coverage.southlimit,
                    spatial_coverage.westlimit,
                ),
                validate_bbox=False,
            )
        elif isinstance(spatial_coverage, PointCoverage):
            # NOTE: Legacy PointCoverage.units has no dedicated GeoCoordinates field; preserved
            # via Place.additionalProperty below instead.
            place.geo = GeoCoordinates.model_construct(
                latitude=spatial_coverage.north,
                longitude=spatial_coverage.east,
            )

        if spatial_reference is not None:
            # NOTE: Legacy BoxSpatialReference/PointSpatialReference.units and
            # BoxSpatialReference.datum have no dedicated SpatialReference
            # fields; preserved via Place.additionalProperty below instead.
            place.srs = cls._to_schema_spatial_reference(spatial_reference)

        # NOTE: 'units' (on spatial_coverage and spatial_reference) and 'datum' (on
        # spatial_reference) have no dedicated field on Place/GeoShape/GeoCoordinates/
        # SpatialReference, so they're round-tripped via Place.additionalProperty.
        # TODO: Consider adding proper 'units' and 'datum' fields to GeoShape/GeoCoordinates/SpatialReference.
        overflow_properties = cls._spatial_overflow_to_additional_properties(spatial_coverage, spatial_reference)
        if overflow_properties:
            place.additionalProperty = overflow_properties

        return place

    @classmethod
    def _to_schema_spatial_reference(cls, spatial_reference: MultidimensionalBoxSpatialReference) -> SpatialReference:
        """Convert MultidimensionalBoxSpatialReference → SpatialReference.
        """
        srs_type = getattr(spatial_reference, "srs_type", None) or "geographic"

        return SpatialReference.model_construct(
            name=getattr(spatial_reference, "projection_name", None)
            or getattr(spatial_reference, "projection", None)
            or cls._DEFAULT_SRS_NAME,
            srsType=srs_type,
            code=getattr(spatial_reference, "projection_string_type", None),
            wktString=getattr(spatial_reference, "projection_string", None),
        )

    # ------------------------------------------------------------------
    # Temporal coverage helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_legacy_period_coverage(
        temporal_coverage: Optional[TemporalCoverage],
    ) -> Optional[PeriodCoverage]:
        """Convert ScientificDataset.temporalCoverage → legacy PeriodCoverage.
        """
        if temporal_coverage is None or temporal_coverage.startDate is None:
            return None
        return PeriodCoverage(start=temporal_coverage.startDate, end=temporal_coverage.endDate)

    @staticmethod
    def _to_schema_temporal_coverage(
        period_coverage: Optional[PeriodCoverage],
    ) -> Optional[TemporalCoverage]:
        if period_coverage is None or period_coverage.start is None:
            return None
        return TemporalCoverage.model_construct(startDate=period_coverage.start, endDate=period_coverage.end)

    # ------------------------------------------------------------------
    # Rights / license helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_legacy_rights(license_data: Any) -> Optional[Rights]:
        if license_data is None:
            return None
        if isinstance(license_data, CreativeWork):
            statement = license_data.name
            url = str(license_data.url) if license_data.url else None
            description = license_data.description
            if not statement and not url and not description:
                # A CreativeWork with nothing set (no name/url/description) carries no rights
                return None
            return Rights(statement=statement, url=url, description=description)
        return Rights(url=str(license_data))

    @staticmethod
    def _to_schema_license(rights: Optional[Rights]) -> Optional[CreativeWork]:
        if rights is None:
            return None
        name = getattr(rights, "statement", None)
        url = str(getattr(rights, "url", None)) if getattr(rights, "url", None) else None
        description = getattr(rights, "description", None)
        if not name and not url and not description:
            # A Rights with nothing set (no statement/url/description) carries no license
            return None
        return CreativeWork.model_construct(name=name, url=url, description=description)

    # ------------------------------------------------------------------
    # additionalProperty ↔ dict helpers
    # (same logic as RasterMetadataAdapter; extracted here to avoid coupling)
    # ------------------------------------------------------------------

    @staticmethod
    def _additional_property_to_dict(additional_property: Any) -> Dict[str, str]:
        """Flatten ScientificDataset.additionalProperty to a plain str→str dict.

        'additionalProperty' is typed as 'Optional[Union[str, List[str], PropertyValue,
        List[PropertyValue]]]', and this
        method handles all of those shapes. It seems, currently no HydroShare content-type
        extractor ever populates 'additionalProperty' at all; the only real
        producer for netcdf is this adapter's own '_dict_to_additional_property', which always
        emits 'List[PropertyValue]' with string-coerced values. So in practice, 'PropertyValue''s
        fields ('propertyID', 'unitCode', 'minValue', 'maxValue', 'measurementTechnique',
        etc.) are not preserved here --
        only 'name' and a stringified 'value' survive the flatten to
        'MultidimensionalMetadata.additional_metadata' (a plain 'Dict[str, str]'). This is
        intentionally left as-is, since nothing currently
        generates those richer shapes for netcdf.
        TODO: To avoid data loss, consider adding the 'additionalProperty' field to the legacy model
        """
        if additional_property is None:
            return {}

        if isinstance(additional_property, PropertyValue):
            return {additional_property.name: str(additional_property.value)}

        if isinstance(additional_property, dict):
            if "name" in additional_property:
                return {str(additional_property.get("name")): str(additional_property.get("value", ""))}
            return {str(key): str(value) for key, value in additional_property.items()}

        if isinstance(additional_property, list):
            result: Dict[str, str] = {}
            value_index = 0
            for item in additional_property:
                if isinstance(item, PropertyValue):
                    result[item.name] = str(item.value)
                elif isinstance(item, dict) and "name" in item:
                    result[str(item.get("name"))] = str(item.get("value", ""))
                elif isinstance(item, str):
                    # A bare string within the list (the List[str] shape) has no "name" of its
                    # own, so give it a synthetic, positional key rather than silently dropping
                    # it.
                    result[f"value_{value_index}"] = item
                    value_index += 1
            return result

        if isinstance(additional_property, str):
            return {"value": additional_property}

        return {}

    @staticmethod
    def _dict_to_additional_property(values: Dict[str, Any]) -> List[PropertyValue]:
        """Convert a plain dict to a list of PropertyValue objects."""
        return [PropertyValue.model_construct(name=key, value=str(value)) for key, value in values.items()]

    @staticmethod
    def _spatial_overflow_to_additional_properties(
        spatial_coverage: Union[BoxCoverage, PointCoverage],
        spatial_reference: Optional[MultidimensionalBoxSpatialReference],
    ) -> List[PropertyValue]:
        """Produce Place.additionalProperty entries for legacy fields with no schema.org equivalent.

        Fields round-tripped this way:
          - 'spatial_coverage.units'   → 'PropertyValue(name="spatial_coverage_units", value=...)'
          - 'spatial_reference.units'  → 'PropertyValue(name="spatial_reference_units", value=...)'
          - 'spatial_reference.datum'  → 'PropertyValue(name="spatial_reference_datum", value=...)'
        TODO: Consider adding these missing fields to schema.org models instead of round-tripping via additionalProperty.
        """
        properties: List[PropertyValue] = []
        if getattr(spatial_coverage, "units", None):
            properties.append(PropertyValue.model_construct(name="spatial_coverage_units", value=spatial_coverage.units))
        if spatial_reference is not None:
            if getattr(spatial_reference, "units", None):
                properties.append(
                    PropertyValue.model_construct(name="spatial_reference_units", value=spatial_reference.units)
                )
            if getattr(spatial_reference, "datum", None):
                properties.append(
                    PropertyValue.model_construct(name="spatial_reference_datum", value=spatial_reference.datum)
                )
        return properties

    # ------------------------------------------------------------------
    # Generic utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_bbox(box: str) -> List[float]:
        """Parse a GeoShape bbox string '"S W N E"' into [north, east, south, west].
        """
        try:
            south, west, north, east = map(float, str(box).split())
        except Exception as e:
            raise ValueError(f"Invalid geo.box string: {box!r}, error: {e}")
        return [north, east, south, west]

    @staticmethod
    def _compose_box(north: float, east: float, south: float, west: float) -> str:
        """Serialise four cardinal limits to a GeoShape bbox string, in the real 'S W N E'
        token order (see _parse_bbox)."""
        return f"{south} {west} {north} {east}"

    @staticmethod
    def _to_str(value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except Exception:
            return None

    @staticmethod
    def _parse_float_or_original(value: Any) -> Optional[Union[float, str]]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except Exception:
            return value
