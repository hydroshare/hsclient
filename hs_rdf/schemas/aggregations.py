from typing import List, Union

from pydantic import AnyUrl, Field, validator, root_validator

from hs_rdf.schemas.base_models import BaseMetadata
from hs_rdf.schemas.fields import BandInformation, CellInformation, FieldInformation, GeometryInformation, Variable, \
    TimeSeriesResult, BoxSpatialReference, MultidimensionalBoxSpatialReference, PointSpatialReference, \
    MultidimensionalPointSpatialReference, PointCoverage, BoxCoverage, PeriodCoverage, Rights
from hs_rdf.schemas.rdf.validators import language_constraint
from hs_rdf.schemas.root_validators import parse_additional_metadata, split_coverages, parse_url
from hs_rdf.schemas.validators import parse_spatial_reference, parse_multidimensional_spatial_reference


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
    type: AnyUrl = Field(const=True, default="GeographicRasterAggregation")

    band_information: BandInformation = Field()
    spatial_reference: Union[BoxSpatialReference, PointSpatialReference] = Field(default=None)
    cell_information: CellInformation = Field()

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(parse_spatial_reference)


class GeographicFeatureMetadata(BaseAggregationMetadata):
    type: AnyUrl = Field(const=True, default="GeographicFeatureAggregation")

    field_information: List[FieldInformation] = Field()
    geometry_information: GeometryInformation = Field()
    spatial_reference: Union[BoxSpatialReference, PointSpatialReference] = Field(default=None)

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(parse_spatial_reference)


class MultidimensionalMetadata(BaseAggregationMetadata):
    type: AnyUrl = Field(const=True, default="MultidimensionalAggregation")

    variables: List[Variable] = Field()
    spatial_reference: Union[MultidimensionalBoxSpatialReference, MultidimensionalPointSpatialReference] = Field(default=None)

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(parse_multidimensional_spatial_reference)


class ReferencedTimeSeriesMetadata(BaseAggregationMetadata):
    type: AnyUrl = Field(const=True, default="ReferencedTimeSeriesAggregation")


class FileSetMetadata(BaseAggregationMetadata):
    type: AnyUrl = Field(const=True, default="FileSetAggregation")


class SingleFileMetadata(BaseAggregationMetadata):
    type: AnyUrl = Field(const=True, default="SingleFileAggregation")


class TimeSeriesMetadata(BaseAggregationMetadata):
    type: AnyUrl = Field(const=True, default="TimeSeriesAggregation")

    time_series_results: List[TimeSeriesResult] = Field()
