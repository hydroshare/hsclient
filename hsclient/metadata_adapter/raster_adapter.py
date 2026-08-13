from __future__ import annotations

"""
Adapter between the locally-owned GeographicRasterMetadata legacy model and the
schema.org-based ScientificDataset.

Conversion directions
---------------------
  to_legacy_geographic_raster_metadata : ScientificDataset | dict → GeographicRasterMetadata
  to_geographic_raster_metadata        : GeographicRasterMetadata | dict → ScientificDataset

CellInformation overflow fields
--------------------------------
'CellInformation.cell_size_x_value' and 'CellInformation.cell_size_y_value' have no dedicated
equivalent in the 'ScientificDataset' or 'Dimension' schema.  They are round-tripped via
'ScientificDataset.additionalProperty' and 'GeographicRasterMetadata.additional_metadata' under the keys:

  'cell_size_x_value'
  'cell_size_y_value'

NOTE: This is a temporary solution until we add a dedicated field for cell size to schema-org based models.
TODO: Consider adding a proper per-dimension size field to the legacy model.

'CellInformation.cell_data_type' does have a natural home on the
schema.org side ('DataVariable.dataType'), so 'DataVariable.dataType' is the single
source for it in both directions —
'_to_schema_variable_measured' sets every band's 'dataType' identically from
'cell_information.cell_data_type' (legacy → schema), and '_to_legacy_cell_information' reads it
back from the first band's 'DataVariable.dataType' (schema → legacy).

BandInformation ↔ variableMeasured mapping
------------------------------------------
Each 'BandInformation' object maps to one 'DataVariable' entry in
'ScientificDataset.variableMeasured'.  The legacy model allows a single
'BandInformation' instance or a list; the adapter normalises both to a list
before converting.

  'BandInformation.name'          ↔ 'DataVariable.name'
  'BandInformation.variable_unit' ↔ 'DataVariable.unit'
  'BandInformation.minimum_value' ↔ 'DataVariable.minValue'
  'BandInformation.maximum_value' ↔ 'DataVariable.maxValue'
  'BandInformation.no_data_value' ↔ 'DataVariable.noDataValue'
  'BandInformation.comment'       ↔ 'DataVariable.description'
  'BandInformation.method'        ↔ 'DataVariable.method'

SpatialReference.srsType ↔ BoxSpatialReference/PointSpatialReference.srs_type
------------------------------------------------------------------------------
'srs_type' is a dedicated field on the legacy spatial reference models (added specifically for
this round trip; it has no equivalent in 'hsmodels'). It is populated directly from
'ScientificDataset.spatialCoverage.srs.srsType' on the schema → legacy leg, and read back
directly on the legacy → schema leg, defaulting to "geographic" if unset.

Dimension ↔ CellInformation mapping
-------------------------------------
'CellInformation.rows' and 'CellInformation.columns' are stored as named
'Dimension' objects ('name="rows"' and 'name="columns"') in
'ScientificDataset.dimensions'.  On the return trip the adapter reconstructs
'CellInformation.rows/columns' by scanning for those exact names.

When more than one band is present, an additional 'Dimension(name="band", shape=<count>)'
is prepended to the dimensions list so that the full raster shape is represented.

Any 'Dimension' named something other than '"rows"'/'"columns"'/'"band"' has no
'GeographicRasterMetadata' equivalent and is dropped on the schema → legacy leg. This is
currently expected -- a raster is not expected to have more than these three dimensions.

Spatial units/datum overflow fields
------------------------------------
'BoxCoverage.units'/'PointCoverage.units', 'BoxSpatialReference.units'/
'PointSpatialReference.units', and 'BoxSpatialReference.datum' already exist on the legacy
models but have no equivalent on 'GeoShape'/'GeoCoordinates'/'SpatialReference' -- unlike
'srsType' above, this is a schema.org-side gap, not a legacy-side one. They are instead round-tripped
via 'Place.additionalProperty' (not 'ScientificDataset.additionalProperty' — this keeps the overflow data
scoped to the spatial object it describes) under the keys:

  'spatial_coverage_units'
  'spatial_reference_units'
  'spatial_reference_datum'

See 'RasterMetadataAdapter._spatial_overflow_to_additional_properties'.
NOTE: This is a temporary solution until we add a dedicated field for spatial units and datum to schema.org based models.
TODO: Consider adding proper 'units' and 'datum' fields to GeoShape/GeoCoordinates/SpatialReference.

 hasPart / isPartOf
-------------------
'ScientificDataset.hasPart'/'isPartOf' had no equivalent on
'legacy GeographicRasterMetadata', so these 2 fields added to GeographicRasterMetadata.
"""

import logging
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
from hsclient.schema.dataset import AdditionalType, DataVariable, Dimension, ScientificDataset
from hsclient.schema.legacy.raster import (
    BandInformation,
    BoxCoverage,
    BoxSpatialReference,
    CellInformation,
    GeographicRasterMetadata,
    PeriodCoverage,
    PointCoverage,
    PointSpatialReference,
    Rights,
)


_logger = logging.getLogger(__name__)


class RasterMetadataAdapter:
    """Translate Geographic Raster metadata between ScientificDataset and the
    locally-owned GeographicRasterMetadata legacy model."""

    _DEFAULT_SRS_NAME = "Unknown spatial reference"

    # ------------------------------------------------------------------
    # Public conversion methods
    # ------------------------------------------------------------------

    @classmethod
    def to_legacy_geographic_raster_metadata(
        cls, metadata: Union[ScientificDataset, Dict[str, Any]]
    ) -> GeographicRasterMetadata:
        """Convert a ScientificDataset (or its dict representation) to GeographicRasterMetadata.
        """
        dataset = metadata if isinstance(metadata, ScientificDataset) else ScientificDataset.model_validate(metadata)

        # NOTE: This is not a permanent solution to handle fields that can't be directly mapped between the 2 metadata formats.
        additional_metadata = cls._additional_property_to_dict(dataset.additionalProperty)

        return GeographicRasterMetadata(
            type=AggregationType.GeographicRasterAggregation,
            title=dataset.name,
            subjects=dataset.keywords or [],
            language=dataset.inLanguage,
            description=dataset.description,
            additional_metadata=additional_metadata,
            spatial_coverage=cls._to_legacy_spatial_coverage(dataset.spatialCoverage),
            period_coverage=cls._to_legacy_period_coverage(dataset.temporalCoverage),
            band_information=cls._to_legacy_band_information(dataset.variableMeasured),
            spatial_reference=cls._to_legacy_spatial_reference(dataset.spatialCoverage),
            cell_information=cls._to_legacy_cell_information(
                dataset.dimensions, additional_metadata, dataset.variableMeasured
            ),
            url=dataset.url,
            rights=cls._to_legacy_rights(dataset.license),
            associatedMedia=dataset.associatedMedia,
            hasPart=dataset.hasPart,
            isPartOf=dataset.isPartOf,
        )

    @classmethod
    def to_geographic_raster_metadata(
        cls, metadata: Union[GeographicRasterMetadata, Dict[str, Any]]
    ) -> ScientificDataset:
        """Convert a GeographicRasterMetadata legacy object (or dict) to a ScientificDataset."""
        if isinstance(metadata, GeographicRasterMetadata):
            legacy = metadata
        else:
            legacy = GeographicRasterMetadata.model_validate(metadata)

        additional_metadata = dict(legacy.additional_metadata or {})
        description = legacy.description
        additional_properties = cls._dict_to_additional_property(additional_metadata)
        # NOTE: This is not a permanent solution to handle fields that can't be directly mapped between the 2 metadata formats.
        additional_properties.extend(cls._cell_information_to_additional_properties(legacy.cell_information))

        return ScientificDataset.model_construct(
            additionalType=AdditionalType.GEOGRAPHIC_RASTER,
            name=legacy.title,
            description=description,
            inLanguage=legacy.language,
            keywords=legacy.subjects or [],
            license=cls._to_schema_license(legacy.rights),
            url=legacy.url,
            additionalProperty=additional_properties,
            spatialCoverage=cls._to_schema_spatial_coverage(
                legacy.spatial_coverage,
                legacy.spatial_reference,
            ),
            temporalCoverage=cls._to_schema_temporal_coverage(legacy.period_coverage),
            variableMeasured=cls._to_schema_variable_measured(
                legacy.band_information,
                legacy.cell_information,
            ),
            dimensions=cls._to_schema_dimensions(
                legacy.cell_information,
                legacy.band_information,
            ),
            associatedMedia=legacy.associatedMedia,
            hasPart=legacy.hasPart,
            isPartOf=legacy.isPartOf,
        )

    # ------------------------------------------------------------------
    # additionalProperty ↔ dict helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _additional_property_to_dict(additional_property: Any) -> Dict[str, str]:
        """Flatten ScientificDataset.additionalProperty to a plain str→str dict.

        'additionalProperty' is typed as 'Optional[Union[str, List[str], PropertyValue,
        List[PropertyValue]]]', and this
        method handles all of those shapes. It seems currently no HydroShare content-type
        extractor ever populates
        'additionalProperty' at all; the only real producer for raster is this adapter's own
        '_dict_to_additional_property', which always emits 'List[PropertyValue]' with
        string-coerced values. So in practice, 'PropertyValue''s fields ('propertyID',
        'unitCode', 'minValue', 'maxValue', 'measurementTechnique', etc.) are not preserved here -- only 'name' and
        a stringified 'value' survive the flatten to 'GeographicRasterMetadata.additional_metadata'
        (a plain 'Dict[str, str]'). This is intentionally left as-is since nothing currently
        generates those richer shapes for raster.
        TODO: To avoid data loss, consider adding the 'additionalProperty' field to the legacy model.
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
            additional_metadata: Dict[str, str] = {}
            value_index = 0
            for item in additional_property:
                if isinstance(item, PropertyValue):
                    additional_metadata[item.name] = str(item.value)
                elif isinstance(item, dict) and "name" in item:
                    additional_metadata[str(item.get("name"))] = str(item.get("value", ""))
                elif isinstance(item, str):
                    # A bare string within the list (the List[str] shape) has no "name" of its
                    # own, so give it a synthetic, positional key rather than silently dropping
                    # it.
                    additional_metadata[f"value_{value_index}"] = item
                    value_index += 1
            return additional_metadata

        if isinstance(additional_property, str):
            return {"value": additional_property}

        return {}

    @staticmethod
    def _dict_to_additional_property(values: Dict[str, Any]) -> List[PropertyValue]:
        """Convert a plain dict to a list of PropertyValue objects."""
        properties: List[PropertyValue] = []
        for key, value in values.items():
            properties.append(PropertyValue.model_construct(name=key, value=str(value)))
        return properties

    # ------------------------------------------------------------------
    # Rights / license helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_legacy_rights(license_data: Any) -> Optional[Rights]:
        """Convert a ScientificDataset license (CreativeWork or URL string) → legacy Rights."""
        if license_data is None:
            return None

        if isinstance(license_data, CreativeWork):
            statement = license_data.name
            url = str(license_data.url) if license_data.url else None
            description = license_data.description
            if not statement and not url and not description:
                # A CreativeWork with nothing set (no name/url/description) carries no rights
                # information at all.
                return None

            # CreativeWork.name/url/description are all optional; a license carrying only a
            # description (e.g. free-text license terms with no formal name) is still a valid
            # rights statement.
            return Rights(statement=statement, url=url, description=description)

        return Rights(url=str(license_data))

    @staticmethod
    def _to_schema_license(rights: Optional[Rights]) -> Optional[CreativeWork]:
        """Convert legacy Rights → CreativeWork for ScientificDataset.license."""
        if rights is None:
            return None
        name = getattr(rights, "statement", None)
        url = str(getattr(rights, "url", None)) if getattr(rights, "url", None) else None
        description = getattr(rights, "description", None)
        if not name and not url and not description:
            return None
        return CreativeWork.model_construct(name=name, url=url, description=description)

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
        # legacy BoxCoverage/PointCoverage models which do. This one
        # field, 'units' is round-tripped via Place.additionalProperty under the key
        # "spatial_coverage_units".
        # TODO: Consider adding a proper 'units' field to GeoShape/GeoCoordinates to avoid this workaround.
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
    ) -> Optional[Union[BoxSpatialReference, PointSpatialReference]]:
        """Convert ScientificDataset.spatialCoverage.srs → BoxSpatialReference or PointSpatialReference.

        Geographic raster aggregations support both box and point spatial references,
        chosen based on the geometry type of the spatial coverage.
        """
        if spatial_coverage is None or spatial_coverage.geo is None:
            return None

        srs = spatial_coverage.srs
        projection = None
        projection_string = ""
        projection_string_type = None
        projection_name = None
        srs_type = None

        if srs is not None:
            projection_name = srs.name
            projection = srs.code or srs.name
            projection_string = srs.wktString or ""
            projection_string_type = srs.code
            srs_type = srs.srsType

        # NOTE: 'units' and 'datum' have no schema.org equivalent - SpatialReference (Place.srs) carries
        # neither, so -- same as 'spatial_coverage_units' above -- they're round-tripped via
        # Place.additionalProperty.
        # TODO: Consider adding proper 'units' and 'datum' fields to GeoShape/GeoCoordinates/SpatialReference.
        overflow = cls._additional_property_to_dict(spatial_coverage.additionalProperty)
        units = overflow.get("spatial_reference_units")
        datum = overflow.get("spatial_reference_datum")

        geo = spatial_coverage.geo
        if isinstance(geo, GeoShape):
            north, east, south, west = cls._parse_bbox(geo.box)
            return BoxSpatialReference(
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

        if isinstance(geo, GeoCoordinates):
            # NOTE: PointSpatialReference has no 'datum' field, so only
            # 'units' applies here.
            return PointSpatialReference(
                type="point",
                name=spatial_coverage.name,
                east=geo.longitude,
                north=geo.latitude,
                units=units,
                projection=projection,
                projection_string=projection_string,
                projection_string_type=projection_string_type,
                projection_name=projection_name,
                srs_type=srs_type,
            )

        return None

    @staticmethod
    def _to_legacy_period_coverage(temporal_coverage: Optional[TemporalCoverage]) -> Optional[PeriodCoverage]:
        """Convert ScientificDataset.temporalCoverage → legacy PeriodCoverage.
        """
        if temporal_coverage is None or temporal_coverage.startDate is None:
            return None
        return PeriodCoverage(start=temporal_coverage.startDate, end=temporal_coverage.endDate)

    # ------------------------------------------------------------------
    # Band / variable helpers
    # ------------------------------------------------------------------

    @classmethod
    def _to_legacy_band_information(
        cls, variable_measured: Optional[List[Union[str, PropertyValue, DataVariable]]]
    ) -> Optional[Union[BandInformation, List[BandInformation]]]:
        """Convert ScientificDataset.variableMeasured → legacy BandInformation (or list thereof).

        Returns a single 'BandInformation' when only one band is present, or a list for
        multi-band rasters, matching the legacy model's field type.
        Returns 'None' when 'variableMeasured' is empty or contains no recognised entries.
        """
        if not variable_measured:
            return None

        bands: List[BandInformation] = []
        for variable in variable_measured:
            if isinstance(variable, DataVariable):
                bands.append(
                    BandInformation(
                        name=variable.name,
                        variable_name=variable.name,
                        variable_unit=variable.unit,
                        no_data_value=cls._to_str(variable.noDataValue),
                        minimum_value=cls._to_str(variable.minValue),
                        maximum_value=cls._to_str(variable.maxValue),
                        comment=variable.description,
                        method=variable.method,
                    )
                )
            elif isinstance(variable, PropertyValue):
                bands.append(BandInformation(name=variable.name, variable_name=variable.name))
            elif isinstance(variable, str):
                bands.append(BandInformation(name=variable, variable_name=variable))

        if not bands:
            return None
        if len(bands) == 1:
            return bands[0]
        return bands

    # ------------------------------------------------------------------
    # Cell information helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_legacy_cell_information(
        dimensions: Optional[List[Dimension]],
        additional_metadata: Dict[str, str],
        variable_measured: Optional[List[Union[str, PropertyValue, DataVariable]]] = None,
    ) -> Optional[CellInformation]:
        """Reconstruct legacy CellInformation from ScientificDataset dimensions/variableMeasured
        and additionalProperty.

        Rows and columns are recovered from named 'Dimension' entries ('name="rows"' /
        'name="columns"'). 'CellInformation.rows'/'.columns' are required (non-Optional) ints
        on the legacy model, so a 'CellInformation' object can only be constructed when *both* are
        recovered.

        - If neither is present, this returns 'None' immediately, without looking at
          cell_size_x_value/cell_size_y_value/cell_data_type at all, since those overflow fields
          have no relevance without a 'CellInformation'. This is a valid empty state (the
          dataset simply has no cell information), so there is nothing to lose by returning
          'None' here.
        - If exactly one of rows/columns is present, this raises 'ValueError' instead of
          returning 'None'. Silently discarding the one real value would be a real data-loss
          bug with Aggregation.save().

        Hydroshare does not currently populate the cell size fields, however, if the user provides
        them as part of the CellInformation using hsclient, the adapter stores them in
        ScientificDataset.additionalProperty for the round-trip to work.
        TODO: Consider adding dedicated fields for cell size fields to the schema.org based models to avoid this workaround.
        """
        rows = None
        columns = None
        for dimension in dimensions or []:
            dim_name = (dimension.name or "").strip().lower()
            if dim_name == "rows":
                rows = dimension.shape
            elif dim_name == "columns":
                columns = dimension.shape
            elif dim_name != "band":
                # "band" is expected and handled separately (its count is re-derived from
                # variableMeasured); anything else is a dimension GeographicRasterMetadata has no
                # slot for - so it's dropped. Logging this case so a future/custom dimension
                # doesn't disappear silently.
                _logger.warning(
                    "Unrecognized raster dimension %r (shape=%r) has no legacy equivalent and is "
                    "being dropped.",
                    dimension.name,
                    dimension.shape,
                )

        if rows is None and columns is None:
            return None
        if rows is None or columns is None:
            raise ValueError(
                f"Inconsistent raster dimensions: rows={rows!r}, columns={columns!r} -- "
                "CellInformation requires both or neither, since a legacy CellInformation object "
                "cannot represent a partial rows/columns pair."
            )

        # NOTE: CellInformation has fields 'cell_size_x_value' and 'cell_size_y_value' that do not
        # have dedicated ScientificDataset attributes as part of Dimension. Though hydroshare does not currently populate
        # these fields as additionalProperty, we are retrieving them from additionalProperty as part of
        # round-trip flow.
        # TODO: Consider adding dedicated fields for cell size fields to the schema.org based models to avoid this workaround.
        cell_size_x_value = RasterMetadataAdapter._parse_float(additional_metadata.get("cell_size_x_value"))
        cell_size_y_value = RasterMetadataAdapter._parse_float(additional_metadata.get("cell_size_y_value"))

        cell_data_type = None
        for variable in variable_measured or []:
            if isinstance(variable, DataVariable) and variable.dataType:
                cell_data_type = variable.dataType
                break

        if cell_size_x_value is None or cell_size_y_value is None or not cell_data_type:
            _logger.warning(
                "CellInformation constructed with incomplete overflow data (cell_size_x_value=%r, "
                "cell_size_y_value=%r, cell_data_type=%r).",
                cell_size_x_value,
                cell_size_y_value,
                cell_data_type,
            )

        return CellInformation(
            rows=rows,
            columns=columns,
            cell_size_x_value=cell_size_x_value,
            cell_size_y_value=cell_size_y_value,
            cell_data_type=cell_data_type,
        )

    @classmethod
    def _to_schema_spatial_coverage(
        cls,
        spatial_coverage: Optional[Union[BoxCoverage, PointCoverage]],
        spatial_reference: Optional[Union[BoxSpatialReference, PointSpatialReference]],
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
        # So they're round-tripped via Place.additionalProperty.
        # TODO: Consider adding proper 'units' and 'datum' fields to GeoShape/GeoCoordinates/SpatialReference
        # to avoid this workaround.
        overflow_properties = cls._spatial_overflow_to_additional_properties(spatial_coverage, spatial_reference)
        if overflow_properties:
            place.additionalProperty = overflow_properties

        return place

    @classmethod
    def _to_schema_spatial_reference(
        cls, spatial_reference: Union[BoxSpatialReference, PointSpatialReference]
    ) -> SpatialReference:
        """Convert legacy BoxSpatialReference or legacy PointSpatialReference → SpatialReference.
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

    @staticmethod
    def _to_schema_temporal_coverage(period_coverage: Optional[PeriodCoverage]) -> Optional[TemporalCoverage]:
        """Convert legacy PeriodCoverage → ScientificDataset.temporalCoverage."""
        if period_coverage is None or period_coverage.start is None:
            return None
        return TemporalCoverage.model_construct(startDate=period_coverage.start, endDate=period_coverage.end)

    @classmethod
    def _to_schema_variable_measured(
        cls,
        band_information: Optional[Union[BandInformation, List[BandInformation]]],
        cell_information: Optional[CellInformation],
    ) -> List[DataVariable]:
        """Convert legacy BandInformation → list of DataVariable objects.

        Each band becomes one 'DataVariable'.  The spatial dimensions ('rows',
        'columns') are derived from 'CellInformation' and attached to every variable
        so that 'DataVariable.dimensions' reflects the 2-D grid structure.

        'cell_data_type' is stored on 'CellInformation'; it is mapped to
        'DataVariable.dataType' for each band since all bands share the same cell type.
        """
        if band_information is None:
            return []

        # Collect dimension names present in CellInformation for all DataVariable entries.
        dimensions: List[str] = []
        if cell_information is not None:
            dimensions = ["rows", "columns"]

        bands = band_information if isinstance(band_information, list) else [band_information]
        variables: List[DataVariable] = []
        for band in bands:
            variables.append(
                DataVariable.model_construct(
                    name=band.name,
                    dimensions=dimensions,
                    description=band.comment,
                    dataType=getattr(cell_information, "cell_data_type", None) if cell_information else None,
                    unit=band.variable_unit,
                    minValue=cls._parse_float_or_original(band.minimum_value),
                    maxValue=cls._parse_float_or_original(band.maximum_value),
                    noDataValue=cls._parse_float_or_original(band.no_data_value),
                    method=band.method,
                )
            )
        return variables

    @staticmethod
    def _to_schema_dimensions(
        cell_information: Optional[CellInformation],
        band_information: Optional[Union[BandInformation, List[BandInformation]]] = None,
    ) -> List[Dimension]:
        """Build the ScientificDataset.dimensions list from legacy CellInformation and BandInformation.

        Produces up to three 'Dimension' objects in order:
          1. 'band'    - only when more than one band is present (shape = band count)
          2. 'rows'    - when 'CellInformation.rows' is set
          3. 'columns' - when 'CellInformation.columns' is set

        On the return trip ('_to_legacy_cell_information') the 'rows' and 'columns'
        entries are matched by name to reconstruct 'CellInformation.rows/columns'.
        """
        dimensions: List[Dimension] = []

        # Determine band count to decide whether a band dimension is needed.
        band_count = 0
        if isinstance(band_information, list):
            band_count = len(band_information)
        elif band_information is not None:
            band_count = 1

        # Only emit a band dimension for multi-band rasters; single-band rasters omit it.
        if band_count > 1:
            dimensions.append(Dimension.model_construct(name="band", shape=band_count))

        if cell_information is not None:
            dimensions.append(Dimension.model_construct(name="rows", shape=cell_information.rows))
            dimensions.append(Dimension.model_construct(name="columns", shape=cell_information.columns))

        return dimensions

    @staticmethod
    def _cell_information_to_additional_properties(cell_information: Optional[CellInformation]) -> List[PropertyValue]:
        """Produce additionalProperty entries for CellInformation fields with no dedicated
        ScientificDataset attribute.

        Fields round-tripped this way:
          - 'cell_size_x_value' → 'PropertyValue(name="cell_size_x_value", value=...)'
          - 'cell_size_y_value' → 'PropertyValue(name="cell_size_y_value", value=...)'

        'cell_data_type' is NOT written here — it round-trips via 'DataVariable.dataType' instead.
        TODO: Consider adding dedicated fields for cell size fields to the schema.org based models to avoid this workaround.
        """
        if cell_information is None:
            return []

        properties = []
        if getattr(cell_information, "cell_size_x_value", None) is not None:
            properties.append(
                PropertyValue.model_construct(name="cell_size_x_value", value=str(cell_information.cell_size_x_value))
            )
        if getattr(cell_information, "cell_size_y_value", None) is not None:
            properties.append(
                PropertyValue.model_construct(name="cell_size_y_value", value=str(cell_information.cell_size_y_value))
            )
        return properties

    @staticmethod
    def _spatial_overflow_to_additional_properties(
        spatial_coverage: Union[BoxCoverage, PointCoverage],
        spatial_reference: Optional[Union[BoxSpatialReference, PointSpatialReference]],
    ) -> List[PropertyValue]:
        """Produce Place.additionalProperty entries for legacy fields with no schema.org equivalent.

        Fields round-tripped this way:
          - 'spatial_coverage.units'   → 'PropertyValue(name="spatial_coverage_units", value=...)'
          - 'spatial_reference.units'  → 'PropertyValue(name="spatial_reference_units", value=...)'
          - 'spatial_reference.datum'  → 'PropertyValue(name="spatial_reference_datum", value=...)'
            (only present on 'BoxSpatialReference' — 'PointSpatialReference' has no 'datum')
        TODO: Consider adding dedicated fields for spatial units and datum to the schema.org based models to avoid this workaround.
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
        return f"{south} {west} {north} {east}"

    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
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

    @staticmethod
    def _to_str(value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)
