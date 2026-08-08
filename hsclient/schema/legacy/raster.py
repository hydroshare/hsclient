from __future__ import annotations

"""
Locally-owned legacy metadata model for Geographic Raster aggregations.

Why a local model instead of importing hsmodels.schemas.aggregations.GeographicRasterMetadata
directly?
  - We need an optional ``description`` field that has no equivalent in the hsmodels model.
  - We need an optional ``associatedMedia`` field for round-tripping aggregation file references.
  - ``BoxSpatialReference`` and ``PointSpatialReference`` positional limits are kept as required
    ``float`` fields (matching hsmodels) while ``BandInformation`` and ``CellInformation`` fields
    are fully Optional to handle incomplete schema payloads without raising validation errors.
  - All local models use extra="allow" via LegacyBaseModel so that unknown upstream fields are
    preserved during round-trips rather than discarded.
TODO: Update hsmodels to support these changes and remove this local model.
"""

from typing import Dict, List, Literal, Optional, Union

from hsmodels.schemas.enums import AggregationType
from pydantic import AnyUrl, Field

from hsclient.schema.base import MediaType

from .common import BoxCoverage, LegacyBaseModel, PeriodCoverage, PointCoverage, Rights

LegacyRasterBaseModel = LegacyBaseModel

__all__ = [
    "BandInformation",
    "BoxCoverage",
    "BoxSpatialReference",
    "CellInformation",
    "GeographicRasterMetadata",
    "LegacyRasterBaseModel",
    "PeriodCoverage",
    "PointCoverage",
    "PointSpatialReference",
    "Rights",
]


class BandInformation(LegacyRasterBaseModel):
    """Local representation of a single raster band's descriptive metadata.

    All fields are Optional here to allow incomplete schema.org payloads to be
    round-tripped without hard validation failures. In hsmodels, ``name`` is
    required; the remaining fields are already optional.
    """

    # name is required in hsmodels but Optional here (relaxed to avoid hard failures
    # on incomplete schema payloads).
    name: Optional[str] = None
    variable_name: Optional[str] = None
    variable_unit: Optional[str] = None
    no_data_value: Optional[str] = None
    maximum_value: Optional[str] = None
    comment: Optional[str] = None
    method: Optional[str] = None
    minimum_value: Optional[str] = None


class BoxSpatialReference(LegacyRasterBaseModel):
    """Bounding-box spatial reference for Geographic Raster aggregations.
    """

    type: Literal["box"] = "box"
    name: Optional[str] = None
    # Required positional limits — raster aggregations must always have a bounding box.
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
    """Point spatial reference for Geographic Raster aggregations.

    Used when the raster data is associated with a single geographic point rather
    than a bounding box. ``east`` and ``north`` are required floats, matching
    hsmodels. There is no ``datum`` field on the point variant.
    """

    type: Literal["point"] = "point"
    name: Optional[str] = None
    # Required point coordinates — east (longitude) and north (latitude).
    east: float
    north: float
    units: Optional[str] = None
    projection: Optional[str] = None
    projection_string: Optional[str] = None
    projection_string_type: Optional[str] = None
    projection_name: Optional[str] = None


class CellInformation(LegacyRasterBaseModel):
    """Grid dimensions and cell-size metadata for a Geographic Raster aggregation.

    ``rows`` and ``columns`` are required integers, matching hsmodels. All other
    fields are Optional to gracefully handle payloads that omit cell-size or
    data-type details.
    """

    name: Optional[str] = None
    # Required grid dimensions — must be present for any valid raster grid.
    rows: int
    columns: int
    cell_size_x_value: Optional[float] = None
    cell_data_type: Optional[str] = None
    cell_size_y_value: Optional[float] = None


class GeographicRasterMetadata(LegacyRasterBaseModel):
    """Locally-owned legacy metadata model for Geographic Raster aggregations.

    This mirrors hsmodels.schemas.aggregations.GeographicRasterMetadata with two additions:
      - ``description``: stores ScientificDataset.description across round-trips.
      - ``associatedMedia``: preserves aggregation file references from ScientificDataset so
        that they survive a full round-trip through this local model.
    """

    type: AggregationType = AggregationType.GeographicRasterAggregation
    title: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    language: Optional[str] = None
    additional_metadata: Dict[str, str] = Field(default_factory=dict)
    # description is not in hsmodels.GeographicRasterMetadata; added here to round-trip
    # ScientificDataset.description without losing it in additional_metadata.
    description: Optional[str] = None
    spatial_coverage: Optional[Union[PointCoverage, BoxCoverage]] = None
    period_coverage: Optional[PeriodCoverage] = None
    band_information: Optional[Union[BandInformation, List[BandInformation]]] = None
    spatial_reference: Optional[Union[BoxSpatialReference, PointSpatialReference]] = None
    cell_information: Optional[CellInformation] = None
    url: Optional[AnyUrl] = None
    rights: Optional[Rights] = None
    # associatedMedia is not in hsmodels.GeographicRasterMetadata; added here to preserve
    # aggregation file references from ScientificDataset across round-trips.
    associatedMedia: Optional[Union[MediaType, List[MediaType]]] = None
