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
    url: AnyUrl = Field()
    title: str = Field()
    subjects: List[str] = Field(default=[])
    language: str = Field(default="eng")
    additional_metadata: dict = Field(default={})
    spatial_coverage: Union[PointCoverage, BoxCoverage] = Field(default=None)
    period_coverage: PeriodCoverage = Field(default=None)
    rights: Rights = Field(default=None)

    _parse_additional_metadata = root_validator(pre=True, allow_reuse=True)(parse_additional_metadata)
    _parse_coverages = root_validator(pre=True, allow_reuse=True)(split_coverages)
    _parse_url = root_validator(pre=True, allow_reuse=True)(parse_url)
    _language_constraint = validator('language', allow_reuse=True)(language_constraint)


class GeographicRasterMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(const=True, default=AggregationType.GeographicRasterAggregation)

    band_information: BandInformation = Field()
    spatial_reference: Union[BoxSpatialReference, PointSpatialReference] = Field(default=None)
    cell_information: CellInformation = Field()

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(parse_spatial_reference)


class GeographicFeatureMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(const=True, default=AggregationType.GeographicFeatureAggregation)

    field_information: List[FieldInformation] = Field()
    geometry_information: GeometryInformation = Field()
    spatial_reference: Union[BoxSpatialReference, PointSpatialReference] = Field(default=None)

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(parse_spatial_reference)


class MultidimensionalMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(const=True, default=AggregationType.MultidimensionalAggregation)

    variables: List[Variable] = Field()
    spatial_reference: Union[MultidimensionalBoxSpatialReference, MultidimensionalPointSpatialReference] = Field(
        default=None
    )

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(
        parse_multidimensional_spatial_reference
    )


class ReferencedTimeSeriesMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(const=True, default=AggregationType.ReferencedTimeSeriesAggregation)


class FileSetMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(const=True, default=AggregationType.FileSetAggregation)


class SingleFileMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(const=True, default=AggregationType.SingleFileAggregation)


class TimeSeriesMetadata(BaseAggregationMetadata):
    type: AggregationType = Field(const=True, default=AggregationType.TimeSeriesAggregation)

    time_series_results: List[TimeSeriesResult] = Field()
