from typing import List

from pydantic import AnyUrl, Field

from hs_rdf.namespaces import RDF, HSTERMS, DC
from hs_rdf.schemas.fields import BandInformation, SpatialReference, CellInformation, ExtendedMetadata, Coverage, Rights
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel


class GeographicRasterMetadata(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.GeographicRasterAggregation)

    band_information: BandInformation = Field(rdf_predicate=HSTERMS.BandInformation)
    spatial_reference: SpatialReference = Field(rdf_predicate=HSTERMS.spatialReference)
    cell_information: CellInformation = Field(rdf_predicate=HSTERMS.CellInformation)
    title: str = Field(rdf_predicate=DC.title)
    subjects: List[str] = Field(rdf_predicate=DC.subject, default=None)
    extended_metadata: List[ExtendedMetadata] = Field(rdf_predicate=HSTERMS.extendedMetadata, default=None)
    coverage: List[Coverage] = Field(rdf_predicate=DC.coverage, default=None)
    rights: List[Rights] = Field(rdf_predicate=DC.rights, default=None)


class GeographicFeatureMetadata(RDFBaseModel):
    # TODO fields haven't been added yet
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.GeographicFeatureAggregation)

    title: str = Field(rdf_predicate=DC.title)


class MultidimensionalMetadata(RDFBaseModel):
    # TODO fields haven't been added yet
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.MultidimensionalAggregation)

    title: str = Field(rdf_predicate=DC.title)


class ReferencedTimeSeriesMetadata(RDFBaseModel):
    # TODO fields haven't been added yet
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.ReferencedTimeSeriesAggregation)

    title: str = Field(rdf_predicate=DC.title)


class FileSetMetadata(RDFBaseModel):
    # TODO fields haven't been added yet
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.FileSetAggregation)

    title: str = Field(rdf_predicate=DC.title)


class SingleFileMetadata(RDFBaseModel):
    # TODO fields haven't been added yet
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.SingleFileAggregation)

    title: str = Field(rdf_predicate=DC.title)
