import uuid
from typing import List

from pydantic import Field, AnyUrl, validator, root_validator

from hs_rdf.namespaces import HSRESOURCE, HSTERMS, RDF, DC, ORE, CITOTERMS
from hs_rdf.schemas.fields import Description, Creator, Contributor, Source, \
    Relation, ExtendedMetadata, Rights, Date, AwardInfo, Coverage, Identifier, \
    Publisher, Format, DateType, CoverageType
from rdflib.term import Identifier as RDFIdentifier

from hs_rdf.schemas.languages_iso import languages
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel


def hs_uid():
    return getattr(HSRESOURCE, uuid.uuid4().hex)


class ResourceMetadata(RDFBaseModel):
    rdf_subject: RDFIdentifier = Field(default_factory=hs_uid)
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.CompositeResource)

    label: str = Field(default="Composite Resource", const=True)

    title: str = Field(rdf_predicate=DC.title)
    description: Description = Field(rdf_predicate=DC.description, default_factory=Description)
    language: str = Field(rdf_predicate=DC.language, default='eng')
    subjects: List[str] = Field(rdf_predicate=DC.subject, default=[])
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.CompositeResource, const=True)
    identifier: Identifier = Field(rdf_predicate=DC.identifier)
    creators: List[Creator] = Field(rdf_predicate=DC.creator)

    contributors: List[Contributor] = Field(rdf_predicate=DC.contributor, default=[])
    sources: List[Source] = Field(rdf_predicate=DC.source, default=[])
    relations: List[Relation] = Field(rdf_predicate=DC.relation, default=[])
    extended_metadatas: List[ExtendedMetadata] = Field(rdf_predicate=HSTERMS.extendedMetadata, default=[])
    rights: Rights = Field(rdf_predicate=DC.rights, default=None)
    dates: List[Date] = Field(rdf_predicate=DC.date)
    award_infos: List[AwardInfo] = Field(rdf_predicate=HSTERMS.awardInfo, default=[])
    coverages: List[Coverage] = Field(rdf_predicate=DC.coverage, default=[])
    formats: List[Format] = Field(rdf_predicate=HSTERMS.Format, default=[])
    publisher: Publisher = Field(rdf_predicate=DC.publisher, default=None)

    @validator('language')
    def language_constraint(cls, language):
        if language not in [code for code, verbose in languages]:
            raise ValueError("language '{}' must be a 3 letter iso language code".format(language))
        return language

    @root_validator
    def identifier_constraint(cls, values):
        identifier, rdf_subject = values.get('identifier'), values.get('rdf_subject')
        assert rdf_subject, "rdf_subject must be provided"
        assert identifier.hydroshare_identifier == rdf_subject, "rdf_subject and identifier.hydroshare_identifier must match"
        return values

    @validator('dates')
    def dates_constraint(cls, dates):
        assert len(dates) >= 2
        created = list(filter(lambda d: d.type == DateType.created, dates))
        assert len(created) == 1
        created = created[0]
        modified = list(filter(lambda d: d.type == DateType.modified, dates))
        assert len(modified) == 1
        modified = modified[0]

        assert modified.value >= created.value
        return dates

    @validator('coverages')
    def coverages_constraint(cls, coverages):
        def one_or_none_of_type(type):
            cov = list(filter(lambda d: d.type == type, coverages))
            assert len(cov) <= 1
        one_or_none_of_type(CoverageType.point)
        one_or_none_of_type(CoverageType.period)
        one_or_none_of_type(CoverageType.box)
        return coverages

    @validator('coverages')
    def coverages_spatial_constraint(cls, coverages):
        contains_point = any(c for c in coverages if c.type == CoverageType.point)
        contains_box = any(c for c in coverages if c.type == CoverageType.box)
        if contains_point:
            assert not contains_box, "Only one type of spatial coverage is allowed, point or box"
        return coverages


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
