from __future__ import annotations

"""
Locally-owned legacy metadata model for Multidimensional (NetCDF) aggregations.

Why a local model instead of importing hsmodels.schemas.aggregations.MultidimensionalMetadata
directly?
  - We need an optional ``description`` field that has no equivalent in the hsmodels model.
  - We need an optional ``associatedMedia`` field for round-tripping aggregation file references.
  - ``Variable.unit`` and ``Variable.type`` must be Optional to handle incomplete schema payloads
    without raising validation errors.
  - All local models use extra="allow" via LegacyBaseModel so that unknown upstream fields are
    preserved during round-trips rather than discarded.
TODO: Update hsmodels to support these changes and remove this local model.
"""

from typing import Dict, List, Literal, Optional, Union

from hsmodels.schemas.enums import AggregationType
from pydantic import AnyUrl, Field

from hsclient.schema.base import MediaType

from .common import BoxCoverage, LegacyBaseModel, PeriodCoverage, PointCoverage, Rights


LegacyNetCDFBaseModel = LegacyBaseModel

__all__ = [
    "BoxCoverage",
    "LegacyNetCDFBaseModel",
    "MultidimensionalBoxSpatialReference",
    "MultidimensionalMetadata",
    "PeriodCoverage",
    "PointCoverage",
    "Rights",
    "Variable",
]


class Variable(LegacyNetCDFBaseModel):
    """Local representation of a single NetCDF variable.

    Differences from hsmodels.schemas.fields.Variable:
      - ``unit`` and ``type`` are Optional (relaxed to avoid hard failures
        on incomplete schema payloads; hsmodels requires both).
      - ``type`` is stored as a plain ``Optional[str]`` rather than the ``VariableType`` enum
        so that unrecognised type strings do not cause validation errors.
    """

    name: Optional[str] = None
    # unit is required in hsmodels but Optional here (relaxed to avoid hard failures on incomplete schema payloads).
    unit: Optional[str] = None
    # type is a VariableType enum in hsmodels; stored as str here (relaxed to avoid hard failures
    # on unknown values coming from schema.org payloads).
    type: Optional[str] = None
    # Space-separated list of dimension names, e.g. "time lat lon".
    # This is a string in hsmodels, not a list of integers.
    shape: Optional[str] = None
    descriptive_name: Optional[str] = None
    method: Optional[str] = None
    missing_value: Optional[str] = None


class MultidimensionalBoxSpatialReference(LegacyNetCDFBaseModel):
    """Local spatial reference for Multidimensional aggregations.

    For Multidimensional aggregations, hsmodels only supports a box-type spatial reference
    (MultidimensionalBoxSpatialReference extends BoxSpatialReference).  There is no
    PointSpatialReference variant.

    All positional limits are Optional here even though hsmodels requires them — this
    allows incomplete schema.org payloads to be round-tripped without hard failures.
    """

    type: Literal["box"] = "box"
    name: Optional[str] = None
    northlimit: Optional[float] = None
    eastlimit: Optional[float] = None
    southlimit: Optional[float] = None
    westlimit: Optional[float] = None
    units: Optional[str] = None
    projection: Optional[str] = None
    projection_string: Optional[str] = None
    projection_string_type: Optional[str] = None
    datum: Optional[str] = None
    projection_name: Optional[str] = None


class MultidimensionalMetadata(LegacyNetCDFBaseModel):
    """Locally-owned legacy metadata model for Multidimensional (NetCDF) aggregations.

    This mirrors hsmodels.schemas.aggregations.MultidimensionalMetadata with two additions:
      - ``description``: stores ScientificDataset.description across round-trips.
      - ``associatedMedia``: preserves aggregation file references from ScientificDataset so
        that they survive a full round-trip through this local model.
    """

    type: AggregationType = AggregationType.MultidimensionalAggregation
    title: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    language: Optional[str] = None
    # description is not in hsmodels.MultidimensionalMetadata; added here to round-trip
    # ScientificDataset.description without losing it in additional_metadata.
    description: Optional[str] = None
    additional_metadata: Dict[str, str] = Field(default_factory=dict)
    spatial_coverage: Optional[Union[PointCoverage, BoxCoverage]] = None
    period_coverage: Optional[PeriodCoverage] = None
    variables: List[Variable] = Field(default_factory=list)
    spatial_reference: Optional[MultidimensionalBoxSpatialReference] = None
    url: Optional[AnyUrl] = None
    rights: Optional[Rights] = None
    # associatedMedia is not in hsmodels.MultidimensionalMetadata; added here to preserve
    # aggregation file references from ScientificDataset across round-trips.
    associatedMedia: Optional[Union[MediaType, List[MediaType]]] = None
