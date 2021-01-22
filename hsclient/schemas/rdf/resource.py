import uuid
from typing import List

from pydantic import AnyUrl, BaseModel, Field, root_validator, validator
from rdflib.term import Identifier as RDFIdentifier

from hsclient.namespaces import CITOTERMS, DC, DCTERMS, HSRESOURCE, HSTERMS, ORE, RDF
from hsclient.schemas.rdf.fields import (
    AwardInfoInRDF,
    ContributorInRDF,
    CoverageInRDF,
    CreatorInRDF,
    DateInRDF,
    DescriptionInRDF,
    ExtendedMetadataInRDF,
    IdentifierInRDF,
    PublisherInRDF,
    RelationInRDF,
    RightsInRDF,
    SourceInRDF,
)
from hsclient.schemas.rdf.root_validators import (
    parse_coverages,
    parse_rdf_dates,
    parse_rdf_extended_metadata,
    rdf_parse_description,
    rdf_parse_rdf_subject,
)
from hsclient.schemas.rdf.validators import (
    coverages_constraint,
    coverages_spatial_constraint,
    dates_constraint,
    language_constraint,
    parse_rdf_sources,
    rdf_parse_identifier,
    sort_creators,
)


def hs_uid():
    return getattr(HSRESOURCE, uuid.uuid4().hex)


class FileMap(BaseModel):
    rdf_subject: RDFIdentifier = Field(default_factory=hs_uid)
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=ORE.Aggregation)

    is_documented_by: AnyUrl = Field(rdf_predicate=CITOTERMS.isDocumentedBy)
    files: List[AnyUrl] = Field(rdf_predicate=ORE.aggregates)
    title: str = Field(rdf_predicate=DC.title)
    is_described_by: AnyUrl = Field(rdf_predicate=ORE.isDescribedBy)


class ResourceMap(BaseModel):
    rdf_subject: RDFIdentifier = Field(default_factory=hs_uid)
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=ORE.ResourceMap)

    describes: FileMap = Field(rdf_predicate=ORE.describes)
    identifier: str = Field(rdf_predicate=DC.identifier, default=None)
    # modified: datetime = Field(rdf_predicate=DCTERMS.modified)
    creator: str = Field(rdf_predicate=DC.creator, default=None)


class ResourceMetadataInRDF(BaseModel):

    rdf_subject: RDFIdentifier = Field(default_factory=hs_uid)
    _parse_rdf_subject = root_validator(pre=True, allow_reuse=True)(rdf_parse_rdf_subject)

    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.CompositeResource)

    label: str = Field(default="Composite Resource", const=True)

    title: str = Field(rdf_predicate=DC.title)
    description: DescriptionInRDF = Field(rdf_predicate=DC.description, default_factory=DescriptionInRDF)
    language: str = Field(rdf_predicate=DC.language, default='eng')
    subjects: List[str] = Field(rdf_predicate=DC.subject, default=[])
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.CompositeResource, const=True)
    identifier: IdentifierInRDF = Field(rdf_predicate=DC.identifier, cont=True)
    creators: List[CreatorInRDF] = Field(rdf_predicate=DC.creator)

    contributors: List[ContributorInRDF] = Field(rdf_predicate=DC.contributor, default=[])
    sources: List[SourceInRDF] = Field(rdf_predicate=DC.source, default=[])
    relations: List[RelationInRDF] = Field(rdf_predicate=DC.relation, default=[])
    extended_metadata: List[ExtendedMetadataInRDF] = Field(rdf_predicate=HSTERMS.extendedMetadata, default=[])
    rights: RightsInRDF = Field(rdf_predicate=DC.rights, default=None)
    dates: List[DateInRDF] = Field(rdf_predicate=DC.date)
    awards: List[AwardInfoInRDF] = Field(rdf_predicate=HSTERMS.awardInfo, default=[])
    coverages: List[CoverageInRDF] = Field(rdf_predicate=DC.coverage, default=[])
    publisher: PublisherInRDF = Field(rdf_predicate=DC.publisher, default=None)
    citation: str = Field(rdf_predicate=DCTERMS.bibliographicCitation)

    _parse_coverages = root_validator(pre=True, allow_reuse=True)(parse_coverages)
    _parse_extended_metadata = root_validator(pre=True, allow_reuse=True)(parse_rdf_extended_metadata)
    _parse_rdf_dates = root_validator(pre=True, allow_reuse=True)(parse_rdf_dates)
    _parse_description = root_validator(pre=True, allow_reuse=True)(rdf_parse_description)

    _parse_identifier = validator("identifier", pre=True, allow_reuse=True)(rdf_parse_identifier)
    _parse_rdf_sources = validator("sources", pre=True, allow_reuse=True)(parse_rdf_sources)

    _language_constraint = validator('language', allow_reuse=True)(language_constraint)
    _dates_constraint = validator('dates', allow_reuse=True)(dates_constraint)
    _coverages_constraint = validator('coverages', allow_reuse=True)(coverages_constraint)
    _coverages_spatial_constraint = validator('coverages', allow_reuse=True)(coverages_spatial_constraint)
    _sort_creators = validator("creators", pre=True)(sort_creators)
