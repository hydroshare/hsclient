from __future__ import annotations

"""
Adapter between the locally-owned MultidimensionalMetadata legacy model and the
schema.org-based ScientificDataset.

Conversion directions
---------------------
  to_legacy_multidimensional_metadata : ScientificDataset | dict → MultidimensionalMetadata
  to_multidimensional_metadata        : MultidimensionalMetadata | dict → ScientificDataset

Variable overflow fields
------------------------
``Variable.descriptive_name`` and ``Variable.method`` have no direct equivalent in
``DataVariable``.  Both are round-tripped via ``ScientificDataset.additionalProperty``
under the keys:

  ``variable_{varname}_descriptive_name``
  ``variable_{varname}_method``

where ``{varname}`` is the variable name with spaces replaced by underscores.

ALTERNATIVE (not implemented): fold both into ``DataVariable.description`` as a formatted
string, e.g. ``"descriptive_name: {dn}; method: {m}"``.  This is simpler but conflates
two semantically distinct fields and requires fragile string parsing on the return trip.
The chosen approach (separate additionalProperty keys) avoids data loss at the cost of
slightly larger additionalProperty lists.

Variable.shape ↔ Dimension mapping
------------------------------------
``Variable.shape`` in the legacy model is a space-separated string of dimension *names*,
e.g. ``"time lat lon"``.  ``ScientificDataset`` represents each dimension as a ``Dimension``
object with a ``name`` (str) and ``shape`` (int).

Legacy → Schema:
  Each unique dimension name across all variables becomes a ``Dimension(name=..., shape=0)``.
  The integer ``shape=0`` is used as a placeholder when the actual dimension size is not
  available in the legacy metadata.  The dimension *name* is preserved so
  that the shape string can be reconstructed on the return trip.

Schema → Legacy:
  ``DataVariable.dimensions`` (list of dimension name strings) is joined with spaces to
  produce ``Variable.shape``.

Variable.type normalisation
---------------------------
``Variable.type`` in the legacy model corresponds to ``hsmodels.schemas.enums.VariableType``.
``DataVariable.dataType`` is a free-form string.  On the schema → legacy path, the adapter
attempts a case-insensitive match against known ``VariableType`` values and falls back to
``"Unknown"`` for unrecognised strings.
"""

from typing import Any, Dict, List, Optional, Union

from hsmodels.schemas.enums import AggregationType, VariableType

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

# Build a case-insensitive lookup from raw string values → canonical VariableType value.
# e.g. {"float": "Float", "unsigned byte": "Unsigned Byte", ...}
_VARIABLE_TYPE_MAP: Dict[str, str] = {vt.value.lower(): vt.value for vt in VariableType}


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

        The ``additionalType`` of the incoming dataset is not validated here; the caller
        (MetadataAdapter / load_json) is responsible for routing only MULTIDIMENSIONAL datasets
        to this method.
        """
        dataset = metadata if isinstance(metadata, ScientificDataset) else ScientificDataset.model_validate(metadata)

        # Start with the flat additionalProperty → dict conversion.
        # Variable overflow keys are extracted inside _schema_to_legacy_variables so that
        # only the *remaining* keys end up in additional_metadata.
        additional_metadata = cls._additional_property_to_dict(dataset.additionalProperty)

        variables = cls._schema_to_legacy_variables(dataset.variableMeasured, additional_metadata)

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
            spatial_reference=cls._to_legacy_spatial_reference(dataset.spatialCoverage),
            url=dataset.url,
            rights=cls._to_legacy_rights(dataset.license),
            associatedMedia=dataset.associatedMedia,
        )

    @classmethod
    def to_multidimensional_metadata(
        cls, metadata: Union[MultidimensionalMetadata, Dict[str, Any]]
    ) -> ScientificDataset:
        """Convert a MultidimensionalMetadata legacy object (or dict) to a ScientificDataset."""
        if isinstance(metadata, MultidimensionalMetadata):
            legacy = metadata
        else:
            legacy = MultidimensionalMetadata.model_validate(metadata)

        additional_metadata = dict(legacy.additional_metadata or {})
        additional_properties = cls._dict_to_additional_property(additional_metadata)

        # Append overflow additionalProperty entries for variable descriptive_name / method.
        for variable in legacy.variables:
            additional_properties.extend(cls._variable_to_overflow_properties(variable))

        return ScientificDataset.model_construct(
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
            dimensions=cls._variable_shape_to_dimensions(legacy.variables),
            associatedMedia=legacy.associatedMedia,
        )

    # ------------------------------------------------------------------
    # Variable conversion helpers
    # ------------------------------------------------------------------

    @classmethod
    def _schema_to_legacy_variables(
        cls,
        variable_measured: Optional[List[Union[str, PropertyValue, DataVariable]]],
        additional_metadata: Dict[str, str],
    ) -> List[Variable]:
        """Convert ScientificDataset.variableMeasured → list of legacy Variable objects.

        Variable overflow fields (descriptive_name, method) are *popped* from
        ``additional_metadata`` so that they are not duplicated in the legacy model's
        ``additional_metadata`` dict.
        """
        if not variable_measured:
            return []

        variables: List[Variable] = []
        for item in variable_measured:
            if isinstance(item, DataVariable):
                var_key = (item.name or "").replace(" ", "_")
                descriptive_name = additional_metadata.pop(f"variable_{var_key}_descriptive_name", None)
                method = additional_metadata.pop(f"variable_{var_key}_method", None)

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
                        type=cls._normalize_variable_type(item.dataType),
                        shape=shape,
                        descriptive_name=descriptive_name,
                        method=method,
                        missing_value=cls._to_str(item.noDataValue),
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

        ``Variable.descriptive_name`` and ``Variable.method`` are *not* stored on the
        DataVariable directly (no corresponding field exists).  They are instead preserved
        via additionalProperty entries produced by ``_variable_to_overflow_properties``.

        ALTERNATIVE: store both in ``DataVariable.description`` as a formatted string,
        e.g. ``f"{descriptive_name}; method: {method}"``.  This avoids extra additionalProperty
        entries but conflates two distinct fields and requires parsing on the return trip.
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
                    # description is intentionally left None here; descriptive_name and method
                    # are stored as additionalProperty entries (see _variable_to_overflow_properties).
                    description=None,
                )
            )
        return result

    @staticmethod
    def _variable_to_overflow_properties(variable: Variable) -> List[PropertyValue]:
        """Produce additionalProperty entries for Variable fields with no DataVariable equivalent.

        Keys follow the convention ``variable_{varname}_{field}`` where ``{varname}`` is the
        variable name with spaces replaced by underscores.

        Fields round-tripped this way:
          - ``descriptive_name`` → ``variable_{varname}_descriptive_name``
          - ``method``           → ``variable_{varname}_method``

        ALTERNATIVE: a nested structure (e.g. JSON-encoded PropertyValue) could encode more
        variable-level metadata, but flat string keys are simpler and consistent with how
        raster CellInformation overflow fields are stored.
        """
        if not variable.name:
            return []
        var_key = variable.name.replace(" ", "_")
        entries: List[PropertyValue] = []
        if variable.descriptive_name is not None:
            entries.append(
                PropertyValue.model_construct(
                    name=f"variable_{var_key}_descriptive_name",
                    value=variable.descriptive_name,
                )
            )
        if variable.method is not None:
            entries.append(
                PropertyValue.model_construct(
                    name=f"variable_{var_key}_method",
                    value=variable.method,
                )
            )
        return entries

    @staticmethod
    def _variable_shape_to_dimensions(variables: List[Variable]) -> List[Dimension]:
        """Derive a deduplicated Dimension list from variable shape strings.

        Each unique dimension name token (across all variables' space-separated ``shape``
        strings) becomes one ``Dimension(name=..., shape=0)``.  Insertion order is preserved.

        ``shape=0`` is used as a placeholder for the integer dimension size, which is not
        stored in the legacy MultidimensionalMetadata model.  Preserving the
        dimension name is what matters for reconstructing Variable.shape on the return trip.
        """
        seen: Dict[str, bool] = {}
        for var in variables:
            for dim_name in (var.shape or "").split():
                if dim_name and dim_name not in seen:
                    seen[dim_name] = True
        return [Dimension.model_construct(name=dim_name, shape=0) for dim_name in seen]

    @classmethod
    def _normalize_variable_type(cls, type_str: Optional[str]) -> Optional[str]:
        """Normalise a free-form type string to a canonical VariableType value.

        Performs a case-insensitive match against known VariableType enum values.
        Falls back to ``VariableType.Unknown`` if the string is not recognised.

        ALTERNATIVE: preserve the raw string instead of falling back to "Unknown".
        This would be lossless but could result in invalid values when the legacy model
        is later serialised to an API endpoint that enforces the VariableType enum.
        """
        if type_str is None:
            return None
        matched = _VARIABLE_TYPE_MAP.get(type_str.lower())
        if matched:
            return matched
        return VariableType.Unknown.value

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

        geo = spatial_coverage.geo
        if isinstance(geo, GeoShape):
            bbox = cls._parse_bbox(geo.box)
            if bbox is None:
                return None
            north, east, south, west = bbox
            # NOTE: GeoShape does not carry units or projection; BoxCoverage.units /
            # BoxCoverage.projection will be None on this conversion path.
            return BoxCoverage(
                type="box",
                name=spatial_coverage.name,
                northlimit=north,
                eastlimit=east,
                southlimit=south,
                westlimit=west,
                units=None,
                projection=None,
            )

        if isinstance(geo, GeoCoordinates):
            # NOTE: GeoCoordinates does not carry units or projection.
            return PointCoverage(
                type="point",
                name=spatial_coverage.name,
                east=geo.longitude,
                north=geo.latitude,
                units=None,
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

        bbox = cls._parse_bbox(geo.box)
        if bbox is None:
            return None
        north, east, south, west = bbox

        srs = spatial_coverage.srs
        projection = None
        projection_string = None
        projection_string_type = None
        projection_name = None

        if srs is not None:
            projection_name = srs.name
            projection = srs.code or srs.name
            projection_string = srs.wktString
            projection_string_type = srs.code

        return MultidimensionalBoxSpatialReference(
            type="box",
            name=spatial_coverage.name,
            northlimit=north,
            eastlimit=east,
            southlimit=south,
            westlimit=west,
            units=None,
            projection=projection,
            projection_string=projection_string,
            projection_string_type=projection_string_type,
            projection_name=projection_name,
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
            # NOTE: Legacy BoxCoverage.units / projection are not preserved in GeoShape.
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
            # NOTE: Legacy PointCoverage.units / projection are not preserved in GeoCoordinates.
            place.geo = GeoCoordinates.model_construct(
                latitude=spatial_coverage.north,
                longitude=spatial_coverage.east,
            )

        if spatial_reference is not None:
            place.srs = cls._to_schema_spatial_reference(spatial_reference)

        return place

    @classmethod
    def _to_schema_spatial_reference(cls, spatial_reference: MultidimensionalBoxSpatialReference) -> SpatialReference:
        """Convert MultidimensionalBoxSpatialReference → SpatialReference.

        NOTE: The legacy model does not carry an explicit geographic/projected enum, so
        ``srsType`` is inferred heuristically from projection text.
        """
        projection = (getattr(spatial_reference, "projection", "") or "").lower()
        projection_name = (getattr(spatial_reference, "projection_name", "") or "").lower()
        srs_type = "geographic"
        projected_tokens = ["utm", "mercator", "albers", "lambert", "state plane", "projected"]
        if any(token in projection for token in projected_tokens) or any(
            token in projection_name for token in projected_tokens
        ):
            srs_type = "projected"

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
        if temporal_coverage is None:
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
            return Rights(
                statement=license_data.name,
                url=str(license_data.url) if license_data.url else None,
            )
        return Rights(url=str(license_data))

    @staticmethod
    def _to_schema_license(rights: Optional[Rights]) -> Optional[CreativeWork]:
        if rights is None:
            return None
        return CreativeWork.model_construct(
            name=getattr(rights, "statement", None),
            url=str(getattr(rights, "url", None)) if getattr(rights, "url", None) else None,
        )

    # ------------------------------------------------------------------
    # additionalProperty ↔ dict helpers
    # (same logic as RasterMetadataAdapter; extracted here to avoid coupling)
    # ------------------------------------------------------------------

    @staticmethod
    def _additional_property_to_dict(additional_property: Any) -> Dict[str, str]:
        """Flatten ScientificDataset.additionalProperty to a plain str→str dict."""
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
            for item in additional_property:
                if isinstance(item, PropertyValue):
                    result[item.name] = str(item.value)
                elif isinstance(item, dict) and "name" in item:
                    result[str(item.get("name"))] = str(item.get("value", ""))
            return result

        if isinstance(additional_property, str):
            return {"value": additional_property}

        return {}

    @staticmethod
    def _dict_to_additional_property(values: Dict[str, Any]) -> List[PropertyValue]:
        """Convert a plain dict to a list of PropertyValue objects."""
        return [PropertyValue.model_construct(name=key, value=str(value)) for key, value in values.items()]

    # ------------------------------------------------------------------
    # Generic utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_bbox(box: str) -> Optional[List[float]]:
        """Parse a GeoShape bbox string ``"N E S W"`` into [north, east, south, west]."""
        if not box:
            return None
        parts = str(box).split()
        if len(parts) != 4:
            return None
        try:
            return [float(p) for p in parts]
        except Exception:
            return None

    @staticmethod
    def _compose_box(north: float, east: float, south: float, west: float) -> str:
        return f"{north} {east} {south} {west}"

    @staticmethod
    def _to_str(value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)
