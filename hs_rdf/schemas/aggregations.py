from typing import List, Union

from pydantic import AnyUrl, Field, BaseModel, validator, PrivateAttr

from hs_rdf.namespaces import RDF, HSTERMS, DC
from hs_rdf.schemas.enums import CoverageType, SpatialReferenceType
from hs_rdf.schemas.fields import BandInformation, SpatialReferenceInRDF, CellInformation, ExtendedMetadataInRDF, \
    CoverageInRDF, \
    RightsInRDF, FieldInformation, GeometryInformation, Variable, BoxSpatialReference, PointSpatialReference
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel
from hs_rdf.schemas.resource import BoxCoverage, PointCoverage, PeriodCoverage
from hs_rdf.schemas.validators import parse_spatial_reference, parse_spatial_coverage, parse_period_coverage, \
    parse_additional_metadata


class BaseAggregationMetadata(RDFBaseModel):
    title: str = Field(rdf_predicate=DC.title)
    subjects: List[str] = Field(rdf_predicate=DC.subject, default=[])
    language: str = Field(rdf_predicate=DC.language, default="eng")
    extended_metadata: List[ExtendedMetadataInRDF] = Field(rdf_predicate=HSTERMS.extendedMetadata, default=[])
    coverages: List[CoverageInRDF] = Field(rdf_predicate=DC.coverage, default=[])
    rights: RightsInRDF = Field(rdf_predicate=DC.rights, default=[])

class GeographicRasterMetadataInRDF(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.GeographicRasterAggregation)

    label: str = Field(const=True, default="Geographic Raster Content: A geographic grid represented by a virtual raster tile (.vrt) file and one or more geotiff (.tif) files")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.GeographicRasterAggregation, const=True)

    band_information: BandInformation = Field(rdf_predicate=HSTERMS.BandInformation)
    spatial_reference: SpatialReferenceInRDF = Field(rdf_predicate=HSTERMS.spatialReference, default=None)
    cell_information: CellInformation = Field(rdf_predicate=HSTERMS.CellInformation)

class GeographicRasterMetadata(BaseModel):
    _rdf_model: GeographicRasterMetadataInRDF = PrivateAttr()

    title: str = Field()
    subjects: List[str] = Field(default=[])
    language: str = Field(default="eng")
    additional_metadata: dict = Field(alias="extended_metadata", default={})
    spatial_coverage: Union[PointCoverage, BoxCoverage] = Field(alias="coverages", default=None)
    period_coverage: PeriodCoverage = Field(alias="coverages", default=None)
    rights: RightsInRDF = Field(default=None)

    band_information: BandInformation = Field()
    spatial_reference: Union[BoxSpatialReference, PointSpatialReference] = Field(default=None)
    cell_information: CellInformation = Field()

    @classmethod
    def parse(cls, metadata_graph, subject=None):
        rdf_metadata = GeographicRasterMetadataInRDF.parse(metadata_graph, subject)
        d = rdf_metadata.dict()
        instance = GeographicRasterMetadata(**d)
        instance._rdf_model=rdf_metadata
        return instance

    _parse_spatial_reference = validator("spatial_reference", pre=True, allow_reuse=True)(parse_spatial_reference)
    _parse_additional_metadata = validator("additional_metadata", pre=True, allow_reuse=True)(parse_additional_metadata)
    _parse_spatial_coverage = validator("spatial_coverage", pre=True, allow_reuse=True)(parse_spatial_coverage)
    _parse_period_coverage = validator("period_coverage", pre=True, allow_reuse=True)(parse_period_coverage)

    def _sync(self):

        exported = self.dict()

        coverages = []
        if self.spatial_coverage:
            coverages.append({"type": CoverageType[self.spatial_coverage.type], "value": str(self.spatial_coverage)})
            del exported['spatial_coverage']
        if self.period_coverage:
            coverages.append({"type": CoverageType.period, "value": str(self.period_coverage)})
            del exported['period_coverage']
        exported['coverages'] = coverages

        if self.spatial_reference:
            exported['spatial_reference'] ={"type": SpatialReferenceType[self.spatial_reference.type], "value": str(self.spatial_reference)}

        if self.additional_metadata:
            exported['extended_metadata'] = [{"key": key, "value": value}
                                              for key, value in self.additional_metadata.items()]
            del exported['additional_metadata']

        updated_rdf = GeographicRasterMetadataInRDF(**exported)
        updated_rdf._rdf_subject = self._rdf_model._rdf_subject


class GeographicFeatureMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.GeographicFeatureAggregation)

    label: str = Field(const=True, default="Geographic Feature Content: The multiple files that are part of a geographic shapefile")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.GeographicFeatureAggregation, const=True)

    field_informations: List[FieldInformation] = Field(rdf_predicate=HSTERMS.FieldInformation)
    geometry_information: GeometryInformation = Field(rdf_predicate=HSTERMS.GeometryInformation)
    spatial_reference: SpatialReferenceInRDF = Field(rdf_predicate=HSTERMS.spatialReference, default=None)


class MultidimensionalMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.MultidimensionalAggregation)

    label: str = Field(const=True, default="Multidimensional Content: A multidimensional dataset represented by a NetCDF file (.nc) and text file giving its NetCDF header content")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.MultidimensionalAggregation, const=True)

    variables: List[Variable] = Field(rdf_predicate=HSTERMS.Variable)
    spatial_reference: SpatialReferenceInRDF = Field(rdf_predicate=HSTERMS.spatialReference, default=None)


class ReferencedTimeSeriesMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.ReferencedTimeSeriesAggregation)

    label: str = Field(const=True, default="Referenced Time Series Content: A reference to one or more time series served from HydroServers outside of HydroShare in WaterML format")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.ReferencedTimeSeriesAggregation, const=True)


class FileSetMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.FileSetAggregation)

    label: str = Field(const=True, default="File Set Content: One or more files with specific metadata")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.FileSetAggregation, const=True)


class SingleFileMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.SingleFileAggregation)

    label: str = Field(const=True, default="Single File Content: A single file with file specific metadata")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.SingleFileAggregation, const=True)
