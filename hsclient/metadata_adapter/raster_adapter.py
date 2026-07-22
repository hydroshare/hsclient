from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from hsmodels.schemas.enums import AggregationType

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

from hsclient.schema.base import CreativeWork, GeoCoordinates, GeoShape, Place, PropertyValue, SpatialReference, TemporalCoverage
from hsclient.schema.dataset import AdditionalType, DataVariable, Dimension, ScientificDataset


class RasterMetadataAdapter:
    """Translate raster metadata between schema.org ScientificDataset and legacy hsmodels."""

    _DEFAULT_SRS_NAME = "Unknown spatial reference"

    @classmethod
    def to_legacy_geographic_raster_metadata(
        cls, metadata: Union[ScientificDataset, Dict[str, Any]]
    ) -> GeographicRasterMetadata:
        data = metadata if isinstance(metadata, dict) else metadata.model_dump(by_alias=True, exclude_none=True)
        dataset = metadata if isinstance(metadata, ScientificDataset) else ScientificDataset.model_validate(metadata)

        additional_metadata = cls._additional_property_to_dict(dataset.additionalProperty)

        return GeographicRasterMetadata(
            type=AggregationType.GeographicRasterAggregation,
            title=dataset.name,
            subjects=dataset.keywords or [],
            language=data.get("inLanguage"),
            description=dataset.description,
            additional_metadata=additional_metadata,
            spatial_coverage=cls._to_legacy_spatial_coverage(dataset.spatialCoverage),
            period_coverage=cls._to_legacy_period_coverage(dataset.temporalCoverage),
            band_information=cls._to_legacy_band_information(dataset.variableMeasured),
            spatial_reference=cls._to_legacy_spatial_reference(dataset.spatialCoverage),
            cell_information=cls._to_legacy_cell_information(dataset.dimensions, additional_metadata),
            url=data.get("url"),
            rights=cls._to_legacy_rights(dataset.license),
        )

    @classmethod
    def to_geographic_raster_metadata(
        cls, metadata: Union[GeographicRasterMetadata, Dict[str, Any]]
    ) -> ScientificDataset:
        if isinstance(metadata, GeographicRasterMetadata):
            legacy = metadata
        else:
            legacy = GeographicRasterMetadata.model_validate(metadata)

        additional_metadata = dict(getattr(legacy, "additional_metadata", {}) or {})
        description = getattr(legacy, "description", None)        
        additional_properties = cls._dict_to_additional_property(additional_metadata)
        additional_properties.extend(
            cls._cell_information_to_additional_properties(getattr(legacy, "cell_information", None))
        )

        return ScientificDataset.model_construct(
            additionalType=AdditionalType.GEOGRAPHIC_RASTER,
            name=getattr(legacy, "title", None),
            description=description,
            inLanguage=getattr(legacy, "language", None),
            keywords=getattr(legacy, "subjects", []) or [],
            license=cls._to_schema_license(getattr(legacy, "rights", None)),
            url=getattr(legacy, "url", None),
            additionalProperty=additional_properties,
            spatialCoverage=cls._to_schema_spatial_coverage(
                getattr(legacy, "spatial_coverage", None),
                getattr(legacy, "spatial_reference", None),
            ),
            temporalCoverage=cls._to_schema_temporal_coverage(getattr(legacy, "period_coverage", None)),
            variableMeasured=cls._to_schema_variable_measured(
                getattr(legacy, "band_information", None),
                getattr(legacy, "cell_information", None),
            ),
            dimensions=cls._to_schema_dimensions(
                getattr(legacy, "cell_information", None),
                getattr(legacy, "band_information", None),
            ),
        )

    @staticmethod
    def _additional_property_to_dict(additional_property: Any) -> Dict[str, str]:
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
            for item in additional_property:
                if isinstance(item, PropertyValue):
                    additional_metadata[item.name] = str(item.value)
                elif isinstance(item, dict) and "name" in item:
                    additional_metadata[str(item.get("name"))] = str(item.get("value", ""))
            return additional_metadata

        if isinstance(additional_property, str):
            return {"value": additional_property}

        return {}

    @staticmethod
    def _dict_to_additional_property(values: Dict[str, Any]) -> List[PropertyValue]:
        properties: List[PropertyValue] = []
        for key, value in values.items():
            properties.append(PropertyValue.model_construct(name=key, value=str(value)))
        return properties

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

    @classmethod
    def _to_legacy_spatial_coverage(
        cls, spatial_coverage: Optional[Place]
    ) -> Optional[Union[BoxCoverage, PointCoverage]]:
        if spatial_coverage is None or spatial_coverage.geo is None:
            return None

        geo = spatial_coverage.geo
        if isinstance(geo, GeoShape):
            bbox = cls._parse_bbox(geo.box)
            if bbox is None:
                return None
            north, east, south, west = bbox
            # NOTE: The schema.org GeoShape does not provide units or projection information,
            # whereas the BoxCoverage (legacy as in hsmodels) requires units and projection is optional.
            # In the ported legacy BoxCoverage, we made both units and projection optional.
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
            # NOTE: The schema.org GeoCoordinates does not provide units or projection information,
            # whereas the PointCoverage (legacy as in hsmodels) requires units and projection.
            # In the ported legacy PointCoverage, we made both units and projection optional.
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
    ) -> Optional[Union[BoxSpatialReference, PointSpatialReference]]:
        if spatial_coverage is None or spatial_coverage.geo is None:
            return None

        srs = spatial_coverage.srs
        projection = None
        projection_string = ""
        projection_string_type = None
        projection_name = None

        if srs is not None:
            projection_name = srs.name
            projection = srs.code or srs.name
            projection_string = srs.wktString or ""
            projection_string_type = srs.code

        geo = spatial_coverage.geo
        if isinstance(geo, GeoShape):
            bbox = cls._parse_bbox(geo.box)
            if bbox is None:
                return None
            north, east, south, west = bbox
            return BoxSpatialReference(
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

        if isinstance(geo, GeoCoordinates):
            return PointSpatialReference(
                type="point",
                name=spatial_coverage.name,
                east=geo.longitude,
                north=geo.latitude,
                units=None,
                projection=projection,
                projection_string=projection_string,
                projection_string_type=projection_string_type,
                projection_name=projection_name,
            )

        return None

    @staticmethod
    def _to_legacy_period_coverage(temporal_coverage: Optional[TemporalCoverage]) -> Optional[PeriodCoverage]:
        if temporal_coverage is None:
            return None
        return PeriodCoverage(start=temporal_coverage.startDate, end=temporal_coverage.endDate)

    @classmethod
    def _to_legacy_band_information(
        cls, variable_measured: Optional[List[Union[str, PropertyValue, DataVariable]]]
    ) -> Optional[Union[BandInformation, List[BandInformation]]]:
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

    @staticmethod
    def _to_legacy_cell_information(
        dimensions: Optional[List[Dimension]], additional_metadata: Dict[str, str]
    ) -> Optional[CellInformation]:
        rows = None
        columns = None
        for dimension in dimensions or []:
            dim_name = (dimension.name or "").strip().lower()
            if dim_name == "rows":
                rows = dimension.shape
            elif dim_name == "columns":
                columns = dimension.shape
        # NOTE: CellInformation has fields 'cell_size_x_value', 'cell_size_y_value', and 'cell_data_type' that do not 
        # have dedicated ScientificDataset attributes as part of Dimension. Though hydroshare does not currently populate 
        # these fields as additionalProperty, we are retrieving them from additionalProperty in case they are present in the future.
        cell_size_x_value = RasterMetadataAdapter._parse_float(additional_metadata.get("cell_size_x_value"))
        cell_size_y_value = RasterMetadataAdapter._parse_float(additional_metadata.get("cell_size_y_value"))
        cell_data_type = additional_metadata.get("cell_data_type")

        if rows is None and columns is None and cell_size_x_value is None and cell_size_y_value is None and not cell_data_type:
            return None

        if rows is None or columns is None:
            return None

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
        if spatial_coverage is None:
            return None

        place = Place.model_construct()
        place.name = getattr(spatial_coverage, "name", None)

        if isinstance(spatial_coverage, BoxCoverage):
            # NOTE: Legacy box coverage includes units/projection fields, but GeoShape stores only bbox geometry.
            # From this adapter's perspective, the units/projection in legacy BoxCoverage will always be set to None
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
            # NOTE: Legacy point coverage includes units/projection fields, but GeoCoordinates stores only lat/lon.
            # From this adapter's perspective, the units/projection in legacy PointCoverage will always be set to None
            place.geo = GeoCoordinates.model_construct(
                latitude=spatial_coverage.north,
                longitude=spatial_coverage.east,
            )

        if spatial_reference is not None:
            place.srs = cls._to_schema_spatial_reference(spatial_reference)

        return place

    @classmethod
    def _to_schema_spatial_reference(
        cls, spatial_reference: Union[BoxSpatialReference, PointSpatialReference]
    ) -> SpatialReference:
        # NOTE: Legacy spatial reference does not carry an explicit geographic/projected enum compatible with
        # ScientificDataset.srs.srsType, so we infer it heuristically from projection text.
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

    @staticmethod
    def _to_schema_temporal_coverage(period_coverage: Optional[PeriodCoverage]) -> Optional[TemporalCoverage]:
        if period_coverage is None or period_coverage.start is None:
            return None
        return TemporalCoverage.model_construct(startDate=period_coverage.start, endDate=period_coverage.end)

    @classmethod
    def _to_schema_variable_measured(
        cls,
        band_information: Optional[Union[BandInformation, List[BandInformation]]],
        cell_information: Optional[CellInformation],
    ) -> List[DataVariable]:
        if band_information is None:
            return []

        dimensions: List[str] = []
        if cell_information is not None:
            if getattr(cell_information, "rows", None) is not None:
                dimensions.append("rows")
            if getattr(cell_information, "columns", None) is not None:
                dimensions.append("columns")

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
                    minValue=cls._parse_float(band.minimum_value),
                    maxValue=cls._parse_float(band.maximum_value),
                    noDataValue=cls._parse_float(band.no_data_value),
                )
            )
        return variables

    @staticmethod
    def _to_schema_dimensions(
        cell_information: Optional[CellInformation],
        band_information: Optional[Union[BandInformation, List[BandInformation]]] = None,
    ) -> List[Dimension]:
        dimensions: List[Dimension] = []

        band_count = 0
        if isinstance(band_information, list):
            band_count = len(band_information)
        elif band_information is not None:
            band_count = 1

        if band_count > 1:
            dimensions.append(Dimension.model_construct(name="band", shape=band_count))

        if cell_information is not None:
            if getattr(cell_information, "rows", None) is not None:
                dimensions.append(Dimension.model_construct(name="rows", shape=cell_information.rows))
            if getattr(cell_information, "columns", None) is not None:
                dimensions.append(Dimension.model_construct(name="columns", shape=cell_information.columns))

        return dimensions

    @staticmethod
    def _cell_information_to_additional_properties(cell_information: Optional[CellInformation]) -> List[PropertyValue]:
        if cell_information is None:
            return []

        # NOTE: CellInformation has fields that do not have dedicated ScientificDataset attributes,
        # so we preserve them as additionalProperty entries.
        properties = []
        if getattr(cell_information, "cell_size_x_value", None) is not None:
            properties.append(
                PropertyValue.model_construct(name="cell_size_x_value", value=str(cell_information.cell_size_x_value))
            )
        if getattr(cell_information, "cell_size_y_value", None) is not None:
            properties.append(
                PropertyValue.model_construct(name="cell_size_y_value", value=str(cell_information.cell_size_y_value))
            )
        if getattr(cell_information, "cell_data_type", None):
            properties.append(
                PropertyValue.model_construct(name="cell_data_type", value=cell_information.cell_data_type)
            )
        return properties

    @staticmethod
    def _parse_bbox(box: str) -> Optional[List[float]]:
        if not box:
            return None
        parts = str(box).split()
        if len(parts) != 4:
            return None
        try:
            return [float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])]
        except Exception:
            return None

    @staticmethod
    def _compose_box(north: float, east: float, south: float, west: float) -> str:
        return f"{north} {east} {south} {west}"

    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except Exception:
            return None

    @staticmethod
    def _to_str(value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)
