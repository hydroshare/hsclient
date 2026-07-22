from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional, Union

from hsmodels.schemas.enums import AggregationType
from pydantic import AnyUrl, BaseModel, ConfigDict, Field, model_validator


class LegacyRasterBaseModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class BandInformation(LegacyRasterBaseModel):
    name: Optional[str] = None
    variable_name: Optional[str] = None
    variable_unit: Optional[str] = None
    no_data_value: Optional[str] = None
    maximum_value: Optional[str] = None
    comment: Optional[str] = None
    method: Optional[str] = None
    minimum_value: Optional[str] = None


class BoxCoverage(LegacyRasterBaseModel):
    type: Literal["box"] = "box"
    name: Optional[str] = None
    northlimit: float
    eastlimit: float
    southlimit: float
    westlimit: float
    units: Optional[str] = None
    projection: Optional[str] = None


class PointCoverage(LegacyRasterBaseModel):
    type: Literal["point"] = "point"
    name: Optional[str] = None
    east: float
    north: float
    units: Optional[str] = None
    projection: Optional[str] = None


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


class PeriodCoverage(LegacyRasterBaseModel):
    name: Optional[str] = None
    start: datetime
    end: Optional[datetime] = None


class Rights(LegacyRasterBaseModel):
    statement: Optional[str] = None
    url: Optional[AnyUrl] = None

    @model_validator(mode="after")
    def validate_statement_or_url_required(self):
        if not (self.statement and self.statement.strip()) and self.url is None:
            raise ValueError("Either 'statement' or 'url' must have a value")
        return self


class GeographicRasterMetadata(LegacyRasterBaseModel):
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
    type: AggregationType = AggregationType.GeographicRasterAggregation
    url: Optional[AnyUrl] = None
    rights: Optional[Rights] = None
