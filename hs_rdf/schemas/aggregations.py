from typing import List, Union

from pydantic import AnyUrl, Field, validator, root_validator, BaseModel

from hs_rdf.namespaces import RDF, HSTERMS, DC
from hs_rdf.schemas.base_models import BaseMetadata
from hs_rdf.schemas.data_structures import BoxSpatialReference, PointSpatialReference, \
    MultidimensionalBoxSpatialReference, MultidimensionalPointSpatialReference
from hs_rdf.schemas.fields import BandInformation, SpatialReferenceInRDF, CellInformation, ExtendedMetadataInRDF, \
    CoverageInRDF, \
    RightsInRDF, FieldInformation, GeometryInformation, Variable, MultidimensionalSpatialReferenceInRDF, \
    BandInformationInRDF, CellInformationInRDF, FieldInformationInRDF, GeometryInformationInRDF, VariableInRDF, Rights, \
    TimeSeriesResultInRDF, TimeSeriesResult
from hs_rdf.schemas.resource import BoxCoverage, PointCoverage, PeriodCoverage
from hs_rdf.schemas.root_validators import parse_coverages, parse_rdf_spatial_reference, rdf_parse_rdf_subject, \
    parse_rdf_extended_metadata, parse_rdf_multidimensional_spatial_reference, split_coverages
from hs_rdf.schemas.validators import parse_spatial_reference, parse_additional_metadata, \
    parse_multidimensional_spatial_reference

from rdflib import BNode
from rdflib.term import Identifier as RDFIdentifier


class BaseAggregationMetadataInRDF(BaseModel):
    rdf_subject: RDFIdentifier = Field(default_factory=BNode)
    _parse_rdf_subject = root_validator(pre=True, allow_reuse=True)(rdf_parse_rdf_subject)
    title: str = Field(rdf_predicate=DC.title)
    subjects: List[str] = Field(rdf_predicate=DC.subject, default=[])
    language: str = Field(rdf_predicate=DC.language, default="eng")
    extended_metadata: List[ExtendedMetadataInRDF] = Field(rdf_predicate=HSTERMS.extendedMetadata, default=[])
    coverages: List[CoverageInRDF] = Field(rdf_predicate=DC.coverage, default=[])
    rights: RightsInRDF = Field(rdf_predicate=DC.rights, default=[])

    _parse_coverages = root_validator(pre=True, allow_reuse=True)(parse_coverages)

    _parse_extended_metadata = root_validator(pre=True, allow_reuse=True)(parse_rdf_extended_metadata)


class GeographicRasterMetadataInRDF(BaseAggregationMetadataInRDF):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.GeographicRasterAggregation)

    label: str = Field(const=True, default="Geographic Raster Content: A geographic grid represented by a virtual "
                                           "raster tile (.vrt) file and one or more geotiff (.tif) files")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.GeographicRasterAggregation, const=True)

    band_information: BandInformationInRDF = Field(rdf_predicate=HSTERMS.BandInformation)
    spatial_reference: SpatialReferenceInRDF = Field(rdf_predicate=HSTERMS.spatialReference, default=None)
    cell_information: CellInformationInRDF = Field(rdf_predicate=HSTERMS.CellInformation)

    _parse_spatial_reference = root_validator(pre=True, allow_reuse=True)(parse_rdf_spatial_reference)


class GeographicFeatureMetadataInRDF(BaseAggregationMetadataInRDF):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.GeographicFeatureAggregation)

    label: str = Field(const=True, default="Geographic Feature Content: The multiple files that are part of a "
                                           "geographic shapefile")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.GeographicFeatureAggregation, const=True)

    field_information: List[FieldInformationInRDF] = Field(rdf_predicate=HSTERMS.FieldInformation)
    geometry_information: GeometryInformationInRDF = Field(rdf_predicate=HSTERMS.GeometryInformation)
    spatial_reference: SpatialReferenceInRDF = Field(rdf_predicate=HSTERMS.spatialReference, default=None)

    _parse_spatial_reference = root_validator(pre=True, allow_reuse=True)(parse_rdf_spatial_reference)


class MultidimensionalMetadataInRDF(BaseAggregationMetadataInRDF):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.MultidimensionalAggregation)

    label: str = Field(const=True, default="Multidimensional Content: A multidimensional dataset represented by a "
                                           "NetCDF file (.nc) and text file giving its NetCDF header content")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.MultidimensionalAggregation, const=True)

    variables: List[VariableInRDF] = Field(rdf_predicate=HSTERMS.Variable)
    spatial_reference: MultidimensionalSpatialReferenceInRDF = Field(rdf_predicate=HSTERMS.spatialReference, default=None)

    _parse_spatial_reference = root_validator(pre=True, allow_reuse=True)(parse_rdf_multidimensional_spatial_reference)


class TimeSeriesMetadataInRDF(BaseAggregationMetadataInRDF):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.TimeSeriesAggregation)

    label: str = Field(const=True, default="Time Series Content: One or more time series held in an ODM2 format "
                                           "SQLite file and optional source comma separated (.csv) files")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.TimeSeriesAggregation, const=True)

    time_series_results: List[TimeSeriesResultInRDF] = Field(rdf_predicate=HSTERMS.timeSeriesResult)


class ReferencedTimeSeriesMetadataInRDF(BaseAggregationMetadataInRDF):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.ReferencedTimeSeriesAggregation)

    label: str = Field(const=True, default="Referenced Time Series Content: A reference to one or more time series "
                                           "served from HydroServers outside of HydroShare in WaterML format")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.ReferencedTimeSeriesAggregation, const=True)


class FileSetMetadataInRDF(BaseAggregationMetadataInRDF):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.FileSetAggregation)

    label: str = Field(const=True, default="File Set Content: One or more files with specific metadata")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.FileSetAggregation, const=True)


class SingleFileMetadataInRDF(BaseAggregationMetadataInRDF):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.SingleFileAggregation)

    label: str = Field(const=True, default="Single File Content: A single file with file specific metadata")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.SingleFileAggregation, const=True)


class BaseAggregationMetadata(BaseMetadata):
    url: AnyUrl = Field(alias="rdf_subject")
    title: str = Field()
    subjects: List[str] = Field(default=[])
    language: str = Field(default="eng")
    additional_metadata: dict = Field(alias="extended_metadata", default={})
    spatial_coverage: Union[PointCoverage, BoxCoverage] = Field(default=None)
    period_coverage: PeriodCoverage = Field(default=None)
    rights: Rights = Field(default=None)

    _parse_additional_metadata = validator("additional_metadata", pre=True, allow_reuse=True)(parse_additional_metadata)
    _parse_coverages = root_validator(pre=True, allow_reuse=True)(split_coverages)


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
