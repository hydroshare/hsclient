import uuid
from datetime import datetime
from typing import List, Union

from pydantic import Field, AnyUrl, validator, root_validator, BaseModel, HttpUrl, PrivateAttr

from hs_rdf.namespaces import HSRESOURCE, HSTERMS, RDF, DC, ORE, CITOTERMS
from hs_rdf.schemas.fields import DescriptionInRDF, CreatorInRDF, ContributorInRDF, SourceInRDF, \
    RelationInRDF, ExtendedMetadataInRDF, RightsInRDF, DateInRDF, AwardInfoInRDF, CoverageInRDF, IdentifierInRDF, \
    PublisherInRDF, FormatInRDF, DateType, CoverageType
from rdflib.term import Identifier as RDFIdentifier

from hs_rdf.schemas.languages_iso import languages
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel


def hs_uid():
    return getattr(HSRESOURCE, uuid.uuid4().hex)


class ORMBaseModel(BaseModel):
    class Config:
        orm_mode = True

class BoxCoverage(BaseModel):
    type: str = "box"
    name: str = None
    northlimit: float
    eastlimit: float
    southlimit: float
    westlimit: float
    units: str
    projection: str


class PointCoverage(BaseModel):
    type: str = "point"
    name: str = None
    east: float
    north: float
    units: str
    projection: str


class PeriodCoverage(BaseModel):
    start: datetime
    end: datetime
    scheme: str = None


class ResourceMetadataInRDF(RDFBaseModel):
    _rdf_subject: RDFIdentifier = PrivateAttr(default_factory=hs_uid)
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.CompositeResource)

    label: str = Field(default="Composite Resource", const=True)

    title: str = Field(rdf_predicate=DC.title)
    description: DescriptionInRDF = Field(rdf_predicate=DC.description, default_factory=DescriptionInRDF)
    language: str = Field(rdf_predicate=DC.language, default='eng')
    subjects: List[str] = Field(rdf_predicate=DC.subject, default=[])
    dc_type: AnyUrl = Field(rdf_predicate=DC.type, default=HSTERMS.CompositeResource, const=True)
    identifier: IdentifierInRDF = Field(rdf_predicate=DC.identifier)
    creators: List[CreatorInRDF] = Field(rdf_predicate=DC.creator)

    contributors: List[ContributorInRDF] = Field(rdf_predicate=DC.contributor, default=[])
    sources: List[SourceInRDF] = Field(rdf_predicate=DC.source, default=[])
    relations: List[RelationInRDF] = Field(rdf_predicate=DC.relation, default=[])
    extended_metadata: List[ExtendedMetadataInRDF] = Field(rdf_predicate=HSTERMS.extendedMetadata, default=[])
    rights: RightsInRDF = Field(rdf_predicate=DC.rights, default=None)
    dates: List[DateInRDF] = Field(rdf_predicate=DC.date)
    award_infos: List[AwardInfoInRDF] = Field(rdf_predicate=HSTERMS.awardInfo, default=[])
    coverages: List[CoverageInRDF] = Field(rdf_predicate=DC.coverage, default=[])
    formats: List[FormatInRDF] = Field(rdf_predicate=HSTERMS.Format, default=[])
    publisher: PublisherInRDF = Field(rdf_predicate=DC.publisher, default=None)

    @validator('language')
    def language_constraint(cls, language):
        if language not in [code for code, verbose in languages]:
            raise ValueError("language '{}' must be a 3 letter iso language code".format(language))
        return language

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


class ResourceMetadata(ORMBaseModel):
    title: str = None
    description: DescriptionInRDF = None
    language: str = None
    subjects: List[str] = []
    creators: List[CreatorInRDF] = []
    contributors: List[ContributorInRDF] = []
    sources: List[SourceInRDF] = Field(rdf_predicate=DC.source, default=[])
    extended_metadata: List[ExtendedMetadataInRDF] = []
    rights: RightsInRDF = Field(rdf_predicate=DC.rights, default=None)
    dates: List[DateInRDF] = Field(rdf_predicate=DC.date)
    award_infos: List[AwardInfoInRDF] = Field(rdf_predicate=HSTERMS.awardInfo, default=[])
    spatial_coverage: Union[BoxCoverage, PointCoverage] = None
    period_coverage: PeriodCoverage = None
    formats: List[FormatInRDF] = Field(rdf_predicate=HSTERMS.Format, default=[])
    publisher: PublisherInRDF = Field(rdf_predicate=DC.publisher, default=None)

    @classmethod
    def parse_rdf_model(self, metadata: ResourceMetadataInRDF):
        md_out = ResourceMetadata.from_orm(metadata)

        def to_coverage_dict(value):
            value_dict = {}
            for key_value in value.split("; "):
                k, v = key_value.split("=")
                value_dict[k] = v
            return value_dict

        for cov in metadata.coverages:
            if cov.type == CoverageType.point:
                md_out.spatial_coverage = PointCoverage(**to_coverage_dict(cov.value))
            elif cov.type == CoverageType.box:
                md_out.spatial_coverage = BoxCoverage(**to_coverage_dict(cov.value))
            elif cov.type == CoverageType.period:
                md_out.period_coverage = PeriodCoverage(**to_coverage_dict(cov.value))
        return md_out


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
