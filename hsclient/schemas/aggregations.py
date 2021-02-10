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
from hsclient.schemas.root_validators import parse_additional_metadata, parse_url, split_coverages, parse_abstract
from hsclient.schemas.validators import parse_multidimensional_spatial_reference, parse_spatial_reference


class BaseAggregationMetadata(BaseMetadata):
    url: AnyUrl = Field(title="TODO Jeff", description="TODO Jeff")
    title: str = Field(title="TODO Jeff", description="TODO Jeff")
    subjects: List[str] = Field(default=[], title="TODO Jeff", description="TODO Jeff")
    language: str = Field(default="eng", title="TODO Jeff", description="TODO Jeff")
    additional_metadata: dict = Field(default={}, title="TODO Jeff", description="TODO Jeff")
    spatial_coverage: Union[PointCoverage, BoxCoverage] = Field(
        default=None, title="TODO Jeff", description="TODO Jeff"
    )
    period_coverage: PeriodCoverage = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    rights: Rights = Field(default=None, title="TODO Jeff", description="TODO Jeff")

    _parse_additional_metadata = root_validator(pre=True, allow_reuse=True)(parse_additional_metadata)
    _parse_coverages = root_validator(pre=True, allow_reuse=True)(split_coverages)
    _parse_url = root_validator(pre=True, allow_reuse=True)(parse_url)
    _language_constraint = validator('language', allow_reuse=True)(language_constraint)


class GeographicRasterMetadata(BaseAggregationMetadata):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: AggregationType = Field(
        const=True, default=AggregationType.GeographicRasterAggregation, title="TODO Jeff", description="TODO Jeff"
    )

    band_information: BandInformation = Field(title="TODO Jeff", description="TODO Jeff")
    spatial_reference: Union[BoxSpatialReference, PointSpatialReference] = Field(
        default=None, title="TODO Jeff", description="TODO Jeff"
    )
    cell_information: CellInformation = Field(title="TODO Jeff", description="TODO Jeff")

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(parse_spatial_reference)


class GeographicFeatureMetadata(BaseAggregationMetadata):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: AggregationType = Field(
        const=True, default=AggregationType.GeographicFeatureAggregation, title="TODO Jeff", description="TODO Jeff"
    )

    field_information: List[FieldInformation] = Field(title="TODO Jeff", description="TODO Jeff")
    geometry_information: GeometryInformation = Field(title="TODO Jeff", description="TODO Jeff")
    spatial_reference: Union[BoxSpatialReference, PointSpatialReference] = Field(
        default=None, title="TODO Jeff", description="TODO Jeff"
    )

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(parse_spatial_reference)


class MultidimensionalMetadata(BaseAggregationMetadata):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: AggregationType = Field(
        const=True, default=AggregationType.MultidimensionalAggregation, title="TODO Jeff", description="TODO Jeff"
    )

    variables: List[Variable] = Field(title="TODO Jeff", description="TODO Jeff")
    spatial_reference: Union[MultidimensionalBoxSpatialReference, MultidimensionalPointSpatialReference] = Field(
        default=None, title="TODO Jeff", description="TODO Jeff"
    )

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(
        parse_multidimensional_spatial_reference
    )


class ReferencedTimeSeriesMetadata(BaseAggregationMetadata):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: AggregationType = Field(
        const=True, default=AggregationType.ReferencedTimeSeriesAggregation, title="TODO Jeff", description="TODO Jeff"
    )


class FileSetMetadata(BaseAggregationMetadata):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: AggregationType = Field(
        const=True, default=AggregationType.FileSetAggregation, title="TODO Jeff", description="TODO Jeff"
    )


class SingleFileMetadata(BaseAggregationMetadata):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: AggregationType = Field(
        const=True, default=AggregationType.SingleFileAggregation, title="TODO Jeff", description="TODO Jeff"
    )


class TimeSeriesMetadata(BaseAggregationMetadata):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: AggregationType = Field(
        const=True, default=AggregationType.TimeSeriesAggregation, title="TODO Jeff", description="TODO Jeff"
    )

    abstract: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    time_series_results: List[TimeSeriesResult] = Field(title="TODO Jeff", description="TODO Jeff")

    _parse_abstract = root_validator(pre=True, allow_reuse=True)(parse_abstract)
