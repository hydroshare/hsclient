import uuid
from typing import List

from pydantic import Field, AnyUrl

from hs_rdf.namespaces import HSRESOURCE, HSTERMS, RDF, DC, ORE, DCTERMS, CITOTERMS
from hs_rdf.schemas.fields import Description, DCType, Creator, Contributor, Source, \
    Relation, ExtendedMetadata, Rights, Date, AwardInfo, Coverage, Identifier
from rdflib.term import Identifier as RDFIdentifier
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel


def hs_uid():
    return getattr(HSRESOURCE, uuid.uuid4().hex)


class ResourceMetadata(RDFBaseModel):
    rdf_subject: RDFIdentifier = Field(default_factory=hs_uid)
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.resource, include=True)

    title: str = Field(rdf_predicate=DC.title, default=None)
    description: Description = Field(rdf_predicate=DC.description, default=None)
    language: str = Field(rdf_predicate=DC.language)
    subjects: List[str] = Field(rdf_predicate=DC.subject, default=[])
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.CompositeResource)
    identifier: Identifier = Field(rdf_predicate=DC.identifier)
    creator: List[Creator] = Field(rdf_predicate=DC.creator)

    contributor: List[Contributor] = Field(rdf_predicate=DC.contributor, default=None)
    source: List[Source] = Field(rdf_predicate=DC.source, default=None)
    relation: List[Relation] = Field(rdf_predicate=DC.relation, default=None)
    extended_metadata: List[ExtendedMetadata] = Field(rdf_predicate=HSTERMS.extendedMetadata, default=None)
    rights: List[Rights] = Field(rdf_predicate=DC.rights, default=None)
    dates: List[Date] = Field(rdf_predicate=DC.date, default=None)
    award_info: List[AwardInfo] = Field(rdf_predicate=HSTERMS.awardInfo, default=None)
    coverage: List[Coverage] = Field(rdf_predicate=DC.coverage, default=None)


class FileMap(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=ORE.Aggregation)

    dc_type: str = Field(rdf_predicate=DCTERMS.type)
    is_documented_by: AnyUrl = Field(rdf_predicate=CITOTERMS.isDocumentedBy)
    files: List[AnyUrl] = Field(rdf_predicate=ORE.aggregates)
    title: str = Field(rdf_predicate=DC.title)
    is_described_by: AnyUrl = Field(rdf_predicate=ORE.isDescribedBy)


class ResourceMap(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=ORE.ResourceMap)

    describes: FileMap = Field(rdf_predicate=ORE.describes)
    identifier: str = Field(rdf_predicate=DC.identifier, default=None)
    #modified: datetime = Field(rdf_predicate=DCTERMS.modified)
    creator: str = Field(rdf_predicate=DC.creator, default=None)
