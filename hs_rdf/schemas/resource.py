import uuid
from typing import List

from pydantic import Field, AnyUrl, validator, root_validator

from hs_rdf.namespaces import HSRESOURCE, HSTERMS, RDF, DC, ORE, DCTERMS, CITOTERMS
from hs_rdf.schemas.fields import Description, DCType, Creator, Contributor, Source, \
    Relation, ExtendedMetadata, Rights, Date, AwardInfo, Coverage, Identifier, \
    Publisher, Format
from rdflib.term import Identifier as RDFIdentifier

from hs_rdf.schemas.languages_iso import languages
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel


def hs_uid():
    return getattr(HSRESOURCE, uuid.uuid4().hex)


class ResourceMetadata(RDFBaseModel):
    rdf_subject: RDFIdentifier = Field(default_factory=hs_uid)
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.CompositeResource, include=True)

    label: str = Field(const=True, default="Composite Resource")

    title: str = Field(rdf_predicate=DC.title, default=None)
    description: Description = Field(rdf_predicate=DC.description, default=None)
    language: str = Field(rdf_predicate=DC.language, default='eng')
    subjects: List[str] = Field(rdf_predicate=DC.subject, default=[])
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.CompositeResource, const=True)
    identifier: Identifier = Field(rdf_predicate=DC.identifier)
    creators: List[Creator] = Field(rdf_predicate=DC.creator)

    contributors: List[Contributor] = Field(rdf_predicate=DC.contributor, default=None)
    sources: List[Source] = Field(rdf_predicate=DC.source, default=None)
    relations: List[Relation] = Field(rdf_predicate=DC.relation, default=None)
    extended_metadatas: List[ExtendedMetadata] = Field(rdf_predicate=HSTERMS.extendedMetadata, default=None)
    rights: Rights = Field(rdf_predicate=DC.rights, default=None)
    dates: List[Date] = Field(rdf_predicate=DC.date, default=None)
    award_infos: List[AwardInfo] = Field(rdf_predicate=HSTERMS.awardInfo, default=None)
    coverages: List[Coverage] = Field(rdf_predicate=DC.coverage, default=None)
    formats: List[Format] = Field(rdf_predicate=HSTERMS.Format, default=None)
    publishers: List[Publisher] = Field(rdf_predicate=HSTERMS.Format, default=None)

    @validator('language')
    def language_constraint(cls, language):
        if language not in [code for code, verbose in languages]:
            raise ValueError("language '{}' must be a 3 letter iso language code".format(language))
        return language

    @root_validator
    def identifier_constraint(cls, values):
        identifier, rdf_subject = values.get('identifier'), values.get('rdf_subject')
        assert identifier.hydroshare_identifier == rdf_subject, "rdf_subject and identifier.hydroshare_identifier must match"
        return values


class FileMap(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=ORE.Aggregation)

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
