from __future__ import annotations

"""
Locally-owned legacy metadata model for Geographic Raster aggregations.

Using this local model for now instead of the external hsmodels.schemas.aggregations.GeographicRasterMetadata
for POC implementation of metadata adapter as it makes it easy to adjust the model to support
round-tripping of ScientificDataset metadata that has no direct equivalent in hsmodels.
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
    # Round-tripped directly from ScientificDataset.spatialCoverage.srs.srsType ("geographic" or
    # "projected"). 'srs_type' is a new field - doesn't exist in hsmodels.
    srs_type: Optional[str] = None


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
    # Round-tripped directly from ScientificDataset.spatialCoverage.srs.srsType ("geographic" or
    # "projected"). 'srs_type' is a new field - doesn't exist in hsmodels.
    srs_type: Optional[str] = None


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

    This mirrors hsmodels.schemas.aggregations.GeographicRasterMetadata with some additional fields as noted below:

    'ScientificDataset.coordinates' represents coordinate axis variables (e.g. lat/lon/time)
    populated by HydroShare's NetCDF extractor for gridded/multidimensional data. Raster
    aggregations have no equivalent concept -- their spatial extent is already fully captured by
    'cell_information' (rows/columns) and 'spatial_reference' (box/point), and their data bands map
    to 'band_information'/'variableMeasured' instead. Nothing currently populates
    'ScientificDataset.coordinates' for raster aggregations. For that reason, 'coordinates'
    is not included in this model.
    """

    type: AggregationType = AggregationType.GeographicRasterAggregation
    title: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    language: Optional[str] = None
    additional_metadata: Dict[str, str] = Field(default_factory=dict)

    # description is not in hsmodels.GeographicRasterMetadata; added here to round-trip
    # ScientificDataset.description.
    description: Optional[str] = None

    spatial_coverage: Optional[Union[PointCoverage, BoxCoverage]] = None
    period_coverage: Optional[PeriodCoverage] = None
    band_information: Optional[Union[BandInformation, List[BandInformation]]] = None
    spatial_reference: Optional[Union[BoxSpatialReference, PointSpatialReference]] = None
    cell_information: Optional[CellInformation] = None
    url: Optional[AnyUrl] = None
    rights: Optional[Rights] = None

    # associatedMedia is not in hsmodels.GeographicRasterMetadata; added here so it survives
    # conversion from ScientificDataset — Aggregation._files() uses it to build the aggregation's
    # File objects (contentUrl/name/checksum/size), so it must remain on this legacy model too.
    # Read-only: users are not allowed to modify this field.
    associatedMedia: Optional[Union[MediaType, List[MediaType]]] = Field(default=None, frozen=True)

    # Read-only capture of ScientificDataset fields with no GeographicRasterMetadata equivalent
    extra_columns: Optional[dict] = Field(default_factory=dict, frozen=True)
