from datetime import datetime
from typing import Dict, List, Union

from pydantic import AnyUrl, Field, root_validator, validator

from hs_rdf.schemas.base_models import BaseMetadata
from hs_rdf.schemas.fields import (
    AwardInfo,
    BoxCoverage,
    Contributor,
    Creator,
    PeriodCoverage,
    PointCoverage,
    Publisher,
    Relation,
    Rights,
)
from hs_rdf.schemas.rdf.validators import language_constraint
from hs_rdf.schemas.root_validators import (
    parse_abstract,
    parse_additional_metadata,
    parse_url,
    split_coverages,
    split_dates,
)
from hs_rdf.schemas.validators import list_not_empty, parse_identifier, parse_sources


class ResourceMetadata(BaseMetadata):
    type: AnyUrl = Field(const=True, default="CompositeResource")

    url: AnyUrl = Field()

    identifier: AnyUrl = Field()
    title: str = Field(max_length=300, default=None, description="The description of a title")
    abstract: str = Field(default=None)
    language: str
    subjects: List[str] = []
    creators: List[Creator] = Field(default=[], description="A list of creators")
    contributors: List[Contributor] = []
    sources: List[str] = Field(default=[])
    relations: List[Relation] = Field(default=[])
    additional_metadata: Dict[str, str] = Field(default={})
    rights: Rights = Field()
    created: datetime = Field(default_factory=datetime.now)
    modified: datetime = Field(default_factory=datetime.now)
    published: datetime = Field(default=None)
    awards: List[AwardInfo] = Field(default=[])
    spatial_coverage: Union[PointCoverage, BoxCoverage] = Field(default=None)
    period_coverage: PeriodCoverage = Field(default=None)
    publisher: Publisher = Field(default=None)
    citation: str = Field(default=None, description="blah")

    _parse_coverages = root_validator(pre=True, allow_reuse=True)(split_coverages)
    _parse_dates = root_validator(pre=True, allow_reuse=True)(split_dates)
    _parse_additional_metadata = root_validator(pre=True, allow_reuse=True)(parse_additional_metadata)
    _parse_abstract = root_validator(pre=True)(parse_abstract)
    _parse_url = root_validator(pre=True, allow_reuse=True)(parse_url)

    _parse_identifier = validator("identifier", pre=True)(parse_identifier)
    _parse_sources = validator("sources", pre=True)(parse_sources)

    _language_constraint = validator('language', allow_reuse=True)(language_constraint)
    _creators_constraint = validator('creators')(list_not_empty)
