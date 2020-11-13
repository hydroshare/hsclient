from typing import List

from pydantic import AnyUrl, Field

from hs_rdf.namespaces import RDF, HSTERMS, DC
from hs_rdf.schemas.fields import BandInformation, SpatialReference, CellInformation, ExtendedMetadata, Coverage, \
    Rights, FieldInformation, GeometryInformation, Variable
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel


class BaseAggregationMetadata(RDFBaseModel):
    title: str = Field(rdf_predicate=DC.title)
    subjects: List[str] = Field(rdf_predicate=DC.subject, default=None)
    language: str = Field(rdf_predicate=DC.language, default=None)
    extended_metadatas: List[ExtendedMetadata] = Field(rdf_predicate=HSTERMS.extendedMetadata, default=None)
    coverages: List[Coverage] = Field(rdf_predicate=DC.coverage, default=None)
    rights: List[Rights] = Field(rdf_predicate=DC.rights, default=None)

class GeographicRasterMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.GeographicRasterAggregation)

    band_information: BandInformation = Field(rdf_predicate=HSTERMS.BandInformation)
    spatial_reference: SpatialReference = Field(rdf_predicate=HSTERMS.spatialReference, default=None)
    cell_information: CellInformation = Field(rdf_predicate=HSTERMS.CellInformation)


class GeographicFeatureMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.GeographicFeatureAggregation)

    field_informations: List[FieldInformation] = Field(rdf_predicate=HSTERMS.FieldInformation)
    geometry_information: GeometryInformation = Field(rdf_predicate=HSTERMS.GeometryInformation)
    spatial_reference: SpatialReference = Field(rdf_predicate=HSTERMS.spatialReference, default=None)


class MultidimensionalMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.MultidimensionalAggregation)

    variables: List[Variable] = Field(rdf_predicate=HSTERMS.Variable)
    spatial_reference: SpatialReference = Field(rdf_predicate=HSTERMS.spatialReference, default=None)


class ReferencedTimeSeriesMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.ReferencedTimeSeriesAggregation)


class FileSetMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.FileSetAggregation)


class SingleFileMetadata(BaseAggregationMetadata):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.SingleFileAggregation)
