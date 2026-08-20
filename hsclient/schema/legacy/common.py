from __future__ import annotations

"""
Shared local legacy field models used across multiple aggregation adapters.

These models are locally owned (not imported from hsmodels) so that:
  - Fields without schema.org equivalents can be made optional without upstream changes.
  - extra="allow" preserves unknown fields during round-trips.

"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import AnyUrl, BaseModel, ConfigDict, model_validator


class LegacyBaseModel(BaseModel):
    """Base model for all locally-owned legacy schema models.

    Uses ``extra="allow"`` so that unknown fields are round-tripped rather than
    raising validation errors.
    """

    model_config = ConfigDict(extra="allow")


class BoxCoverage(LegacyBaseModel):
    """Spatial coverage expressed as a bounding box.

    NOTE: The original hsmodels BoxCoverage requires ``units`` and makes
    ``projection`` optional.  Both are made optional here because schema.org
    GeoShape stores only bbox geometry and carries no units or projection text.
    """

    type: Literal["box"] = "box"
    name: Optional[str] = None
    northlimit: float
    eastlimit: float
    southlimit: float
    westlimit: float
    units: Optional[str] = None
    projection: Optional[str] = None


class PointCoverage(LegacyBaseModel):
    """Spatial coverage expressed as a single point.

    NOTE: Same optionality relaxation as BoxCoverage — ``units`` and
    ``projection`` are optional here even though hsmodels requires them.
    """

    type: Literal["point"] = "point"
    name: Optional[str] = None
    east: float
    north: float
    units: Optional[str] = None
    projection: Optional[str] = None


class PeriodCoverage(LegacyBaseModel):
    """Temporal coverage expressed as a start / end date range."""

    name: Optional[str] = None
    start: datetime
    end: Optional[datetime] = None


class Rights(LegacyBaseModel):
    """License or rights statement attached to an aggregation.

    At least one of ``statement``, ``url``, or ``description`` must be provided.
    """

    statement: Optional[str] = None
    url: Optional[AnyUrl] = None

    # Added so a ScientificDataset license carrying only a CreativeWork.description (no name,
    # no url -- e.g. free-text license terms with no formal name) can round-trip through this
    # model without being dropped or raising a validation error.
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_statement_or_url_or_description_required(self) -> Rights:
        has_statement = bool(self.statement and self.statement.strip())
        has_description = bool(self.description and self.description.strip())
        if not has_statement and self.url is None and not has_description:
            raise ValueError("Either 'statement', 'url', or 'description' must have a value")
        return self
