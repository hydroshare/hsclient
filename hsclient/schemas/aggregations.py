from typing import List, Union

from pydantic import AnyUrl, Field, root_validator, validator

from hsclient.schemas.base_models import BaseMetadata
from hsclient.schemas.enums import AggregationType
from hsclient.schemas.fields import (
    BandInformation,
    BoxCoverage,
    BoxSpatialReference,
    CellInformation,
    FieldInformation,
    GeometryInformation,
    MultidimensionalBoxSpatialReference,
    MultidimensionalPointSpatialReference,
    PeriodCoverage,
    PointCoverage,
    PointSpatialReference,
    Rights,
    TimeSeriesResult,
    Variable,
)
from hsclient.schemas.rdf.validators import language_constraint
from hsclient.schemas.root_validators import parse_additional_metadata, parse_url, split_coverages
from hsclient.schemas.validators import parse_multidimensional_spatial_reference, parse_spatial_reference


class BaseAggregationMetadata(BaseMetadata):
    url: AnyUrl = Field(description="TODO Jeff", title="TODO Jeff")
    title: str = Field(description="TODO Jeff", title="TODO Jeff")
    subjects: List[str] = Field(default=[], description="TODO Jeff", title="TODO Jeff")
    language: str = Field(default="eng", description="TODO Jeff", title="TODO Jeff")
    additional_metadata: dict = Field(default={}, description="TODO Jeff", title="TODO Jeff")
    spatial_coverage: Union[PointCoverage, BoxCoverage] = Field(
        default=None, description="TODO Jeff", title="TODO Jeff"
    )
    period_coverage: PeriodCoverage = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    rights: Rights = Field(default=None, description="TODO Jeff", title="TODO Jeff")

    _parse_additional_metadata = root_validator(pre=True, allow_reuse=True)(parse_additional_metadata)
    _parse_coverages = root_validator(pre=True, allow_reuse=True)(split_coverages)
    _parse_url = root_validator(pre=True, allow_reuse=True)(parse_url)
    _language_constraint = validator('language', allow_reuse=True)(language_constraint)


class GeographicRasterMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(
        const=True, default=AggregationType.GeographicRasterAggregation, description="TODO Jeff", title="TODO Jeff"
    )

    band_information: BandInformation = Field(description="TODO Jeff", title="TODO Jeff")
    spatial_reference: Union[BoxSpatialReference, PointSpatialReference] = Field(
        default=None, description="TODO Jeff", title="TODO Jeff"
    )
    cell_information: CellInformation = Field(description="TODO Jeff", title="TODO Jeff")

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(parse_spatial_reference)


class GeographicFeatureMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(
        const=True, default=AggregationType.GeographicFeatureAggregation, description="TODO Jeff", title="TODO Jeff"
    )

    field_information: List[FieldInformation] = Field(description="TODO Jeff", title="TODO Jeff")
    geometry_information: GeometryInformation = Field(description="TODO Jeff", title="TODO Jeff")
    spatial_reference: Union[BoxSpatialReference, PointSpatialReference] = Field(
        default=None, description="TODO Jeff", title="TODO Jeff"
    )

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(parse_spatial_reference)


class MultidimensionalMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(
        const=True, default=AggregationType.MultidimensionalAggregation, description="TODO Jeff", title="TODO Jeff"
    )

    variables: List[Variable] = Field(description="TODO Jeff", title="TODO Jeff")
    spatial_reference: Union[MultidimensionalBoxSpatialReference, MultidimensionalPointSpatialReference] = Field(
        default=None, description="TODO Jeff", title="TODO Jeff"
    )

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(
        parse_multidimensional_spatial_reference
    )


class ReferencedTimeSeriesMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(
        const=True, default=AggregationType.ReferencedTimeSeriesAggregation, description="TODO Jeff", title="TODO Jeff"
    )


class FileSetMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(
        const=True, default=AggregationType.FileSetAggregation, description="TODO Jeff", title="TODO Jeff"
    )


class SingleFileMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(
        const=True, default=AggregationType.SingleFileAggregation, description="TODO Jeff", title="TODO Jeff"
    )


class TimeSeriesMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(
        const=True, default=AggregationType.TimeSeriesAggregation, description="TODO Jeff", title="TODO Jeff"
    )

    time_series_results: List[TimeSeriesResult] = Field(description="TODO Jeff", title="TODO Jeff")
