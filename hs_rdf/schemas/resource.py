import uuid
from datetime import datetime
from typing import List, Union, Any

from pydantic import Field, AnyUrl, validator, root_validator, BaseModel, HttpUrl, PrivateAttr

from hs_rdf.namespaces import HSRESOURCE, HSTERMS, RDF, DC, ORE, CITOTERMS
from hs_rdf.schemas.fields import DescriptionInRDF, CreatorInRDF, ContributorInRDF, SourceInRDF, \
    RelationInRDF, ExtendedMetadataInRDF, RightsInRDF, DateInRDF, AwardInfoInRDF, CoverageInRDF, IdentifierInRDF, \
    PublisherInRDF, FormatInRDF, DateType, CoverageType
from rdflib.term import Identifier as RDFIdentifier

from hs_rdf.schemas.languages_iso import languages
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel
from hs_rdf.utils import to_coverage_dict


def hs_uid():
    return getattr(HSRESOURCE, uuid.uuid4().hex)


class ORMBaseModel(BaseModel):
    class Config:
        orm_mode = True

class BaseCoverage(BaseModel):

    def __str__(self):
        return "; ".join(["=".join([key, val.isoformat() if isinstance(val, datetime) else str(val)])
                          for key, val in self.__dict__.items()
                          if key != "type" and val])


class BoxCoverage(BaseCoverage):
    type: str = "box"
    name: str = None
    northlimit: float
    eastlimit: float
    southlimit: float
    westlimit: float
    units: str
    projection: str


class BoxSpatialReference(BoxCoverage):
    projection_string: str
    projection_string_type: str = None


class PointCoverage(BaseCoverage):
    type: str = "point"
    name: str = None
    east: float
    north: float
    units: str
    projection: str


class PointSpatialReference(PointCoverage):
    projection_string: str
    projection_string_type: str = None


class PeriodCoverage(BaseCoverage):
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


class Creator(RDFBaseModel):
    name: str = Field()

    creator_order: int
    email: str = Field(default=None)
    organization: str = Field(default=None)

class ResourceMetadata(ORMBaseModel):
    _rdf_model: ResourceMetadataInRDF = PrivateAttr()

    class Config:
        validate_assignment = True

    type: AnyUrl = Field(alias="dc_type")
    identifier: AnyUrl
    title: str = None
    abstract: str = Field(alias="description", default=None)
    language: str = None
    subjects: List[str] = []
    creators: List[Creator] = []
    contributors: List[ContributorInRDF] = []
    derived_from: List[str] = Field(alias="sources", default=[])
    relations: List[RelationInRDF] = Field(default=[])
    additional_metadata = Field(alias="extended_metadata", default={})
    rights: RightsInRDF = Field(default=None)
    created: datetime = Field(alias="dates", default_factory=datetime.now)
    modified: datetime = Field(alias="dates", default_factory=datetime.now)
    published: datetime = Field(alias="dates", default=None)
    award_infos: List[AwardInfoInRDF] = Field(default=[])
    spatial_coverage: Union[BoxCoverage, PointCoverage] = Field(alias='coverages', default=None)
    period_coverage: PeriodCoverage = Field(alias='coverages', default=None)
    file_formats: List[str] = Field(alias='formats', default=[])
    publisher: PublisherInRDF = Field(default=None)

    @validator("identifier", pre=True)
    def parse_identifier(cls, value):
        if isinstance(value, dict) and "hydroshare_identifier" in value:
            return value['hydroshare_identifier']
        return value

    @validator("abstract", pre=True)
    def parse_abstract(cls, value):
        if isinstance(value, dict) and "abstract" in value:
            return value['abstract']
        return value

    @validator("created", pre=True)
    def parse_created(cls, value):
        if isinstance(value, list):
            for date in value:
                if date['type'] == DateType.created:
                    return date['value']
            return None
        return value

    @validator("modified", pre=True)
    def parse_modified(cls, value):
        if isinstance(value, list):
            for date in value:
                if date['type'] == DateType.modified:
                    return date['value']
            return None
        return value

    @validator("published", pre=True)
    def parse_published(cls, value):
        if isinstance(value, list):
            for date in value:
                if date['type'] == DateType.published:
                    return date['value']
            return None
        return value

    @validator("spatial_coverage", pre=True)
    def parse_spatial_coverage(cls, value):
        if isinstance(value, list):
            for coverage in value:
                if coverage['type'] == CoverageType.box:
                    return BoxCoverage(**to_coverage_dict(coverage['value']))
                if coverage['type'] == CoverageType.point:
                    return PointCoverage(**to_coverage_dict(coverage['value']))
            return None
        return value

    @validator("period_coverage", pre=True)
    def parse_period_coverage(cls, value):
        if isinstance(value, list):
            for coverage in value:
                if coverage['type'] == CoverageType.period:
                    return PeriodCoverage(**to_coverage_dict(coverage['value']))
            return None
        return value

    @validator("file_formats", pre=True)
    def parse_file_formats(cls, value):
        if len(value) > 0 and isinstance(value[0], dict):
            return [f['value'] for f in value]
        return value

    @validator("additional_metadata", pre=True)
    def parse_additional_metadata(cls, value):
        if isinstance(value, list):
            parsed = {}
            for em in value:
                parsed[em['key']] = em['value']
            return parsed
        return value

    @validator("derived_from", pre=True)
    def parse_derived_from(cls, value):
        if len(value) > 0 and isinstance(value[0], dict):
            return [f['is_derived_from'] for f in value]
        return value

    @validator('language')
    def language_constraint(cls, language):
        if language not in [code for code, verbose in languages]:
            raise ValueError("language '{}' must be a 3 letter iso language code".format(language))
        return language

    def rdf_string(self, rdf_format='ttl'):
        self._sync()
        return self._rdf_model.rdf_string(rdf_format)

    @classmethod
    def parse(cls, metadata_graph, subject=None):
        rdf_metadata = ResourceMetadataInRDF.parse(metadata_graph, subject)
        instance = ResourceMetadata(**rdf_metadata.dict())
        instance._rdf_model=rdf_metadata
        return instance

    @classmethod
    def parse_file(cls, file, file_format='ttl', subject=None):
        rdf_metadata = ResourceMetadataInRDF.parse_file(file, file_format, subject)
        instance = ResourceMetadata(**rdf_metadata.dict())
        instance._rdf_model=rdf_metadata
        return instance

    def _sync(self):
        # we could check for changes here
        exported = self.dict()

        exported["identifier"] = {"hydroshare_identifier": self.identifier}

        exported["description"] = {"abstract": self.abstract}
        del exported["abstract"]

        dates = []
        dates.append({"type": DateType.created, "value": self.created})
        del exported["created"]
        dates.append({"type": DateType.modified, "value": self.modified})
        del exported["modified"]
        if self.published:
            dates.append({"type": DateType.published, "value": self.published})
            del exported["published"]
        exported["dates"] = dates

        coverages = []
        if self.spatial_coverage:
            coverages.append({"type": CoverageType[self.spatial_coverage.type], "value": str(self.spatial_coverage)})
            del exported['spatial_coverage']
        if self.period_coverage:
            coverages.append({"type": CoverageType.period, "value": str(self.period_coverage)})
            del exported['period_coverage']
        exported['coverages'] = coverages

        if self.file_formats:
            exported['formats'] = [{"value": f} for f in self.file_formats]
            del exported["file_formats"]

        if self.additional_metadata:
            exported['extended_metadata'] = [{"key": key, "value": value}
                                             for key, value in self.additional_metadata.items()]
            del exported['additional_metadata']

        if self.derived_from:
            exported['sources'] = [{"is_derived_from": s} for s in self.derived_from]
            del exported['derived_from']

        updated_rdf = ResourceMetadataInRDF(**exported)
        updated_rdf._rdf_subject = self._rdf_model._rdf_subject
        self._rdf_model = updated_rdf


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
