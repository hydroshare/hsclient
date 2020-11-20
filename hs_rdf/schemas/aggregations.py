from typing import List

from pydantic import AnyUrl, Field

from hs_rdf.namespaces import RDF, HSTERMS, DC
from hs_rdf.schemas.fields import BandInformation, SpatialReference, CellInformation, ExtendedMetadataInRDF, CoverageInRDF, \
    RightsInRDF, FieldInformation, GeometryInformation, Variable
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel


class BaseAggregationMetadata(RDFBaseModel):
    title: str = Field(rdf_predicate=DC.title)
    subjects: List[str] = Field(rdf_predicate=DC.subject, default=None)
    language: str = Field(rdf_predicate=DC.language, default=None)
    extended_metadatas: List[ExtendedMetadataInRDF] = Field(rdf_predicate=HSTERMS.extendedMetadata, default=None)
    coverages: List[CoverageInRDF] = Field(rdf_predicate=DC.coverage, default=None)
    rights: List[RightsInRDF] = Field(rdf_predicate=DC.rights, default=None)

class GeographicRasterMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.GeographicRasterAggregation)

    label: str = Field(const=True, default="Geographic Raster Content: A geographic grid represented by a virtual raster tile (.vrt) file and one or more geotiff (.tif) files")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.GeographicRasterAggregation, const=True)

    band_information: BandInformation = Field(rdf_predicate=HSTERMS.BandInformation)
    spatial_reference: SpatialReference = Field(rdf_predicate=HSTERMS.spatialReference, default=None)
    cell_information: CellInformation = Field(rdf_predicate=HSTERMS.CellInformation)


class GeographicFeatureMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.GeographicFeatureAggregation)

    label: str = Field(const=True, default="Geographic Feature Content: The multiple files that are part of a geographic shapefile")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.GeographicFeatureAggregation, const=True)

    field_informations: List[FieldInformation] = Field(rdf_predicate=HSTERMS.FieldInformation)
    geometry_information: GeometryInformation = Field(rdf_predicate=HSTERMS.GeometryInformation)
    spatial_reference: SpatialReference = Field(rdf_predicate=HSTERMS.spatialReference, default=None)


class MultidimensionalMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.MultidimensionalAggregation)

    label: str = Field(const=True, default="Multidimensional Content: A multidimensional dataset represented by a NetCDF file (.nc) and text file giving its NetCDF header content")
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.MultidimensionalAggregation, const=True)

    variables: List[Variable] = Field(rdf_predicate=HSTERMS.Variable)
    spatial_reference: SpatialReference = Field(rdf_predicate=HSTERMS.spatialReference, default=None)


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
