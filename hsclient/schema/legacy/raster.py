from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

from hsmodels.schemas.enums import AggregationType
from pydantic import AnyUrl, Field

from hsclient.schema.base import MediaType

# ---------------------------------------------------------------------------
# Shared field models live in common.py.
# ---------------------------------------------------------------------------
from .common import BoxCoverage, LegacyBaseModel, PeriodCoverage, PointCoverage, Rights

LegacyRasterBaseModel = LegacyBaseModel


class BandInformation(LegacyRasterBaseModel):
    name: Optional[str] = None
    variable_name: Optional[str] = None
    variable_unit: Optional[str] = None
    no_data_value: Optional[str] = None
    maximum_value: Optional[str] = None
    comment: Optional[str] = None
    method: Optional[str] = None
    minimum_value: Optional[str] = None


class BoxSpatialReference(LegacyRasterBaseModel):
    type: Literal["box"] = "box"
    name: Optional[str] = None
    northlimit: float
    eastlimit: float
    southlimit: float
    westlimit: float
    units: Optional[str] = None
    projection: Optional[str] = None
    projection_string: Optional[str] = None
    projection_string_type: Optional[str] = None
    datum: Optional[str] = None
    projection_name: Optional[str] = None


class PointSpatialReference(LegacyRasterBaseModel):
    type: Literal["point"] = "point"
    name: Optional[str] = None
    east: float
    north: float
    units: Optional[str] = None
    projection: Optional[str] = None
    projection_string: Optional[str] = None
    projection_string_type: Optional[str] = None
    projection_name: Optional[str] = None


class CellInformation(LegacyRasterBaseModel):
    name: Optional[str] = None
    rows: int
    columns: int
    cell_size_x_value: Optional[float] = None
    cell_data_type: Optional[str] = None
    cell_size_y_value: Optional[float] = None


class GeographicRasterMetadata(LegacyRasterBaseModel):
    type: AggregationType = AggregationType.GeographicRasterAggregation
    title: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    language: Optional[str] = None
    additional_metadata: Dict[str, str] = Field(default_factory=dict)
    description: Optional[str] = None
    spatial_coverage: Optional[Union[PointCoverage, BoxCoverage]] = None
    period_coverage: Optional[PeriodCoverage] = None
    band_information: Optional[Union[BandInformation, List[BandInformation]]] = None
    spatial_reference: Optional[Union[BoxSpatialReference, PointSpatialReference]] = None
    cell_information: Optional[CellInformation] = None
    url: Optional[AnyUrl] = None
    rights: Optional[Rights] = None

    # associatedMedia is not part of the original HydroShare legacy raster metadata model,
    # but it is included here to support the new schema.org-based raster metadata model
    # as aggregation data files are represented as associatedMedia items.
    associatedMedia: Optional[Union[MediaType, List[MediaType]]] = None
