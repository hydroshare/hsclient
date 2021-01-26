from datetime import datetime
from typing import Dict, List, Union

from pydantic import AnyUrl, Field, root_validator, validator

from hsclient.schemas.base_models import BaseMetadata
from hsclient.schemas.fields import (
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
from hsclient.schemas.rdf.validators import language_constraint
from hsclient.schemas.root_validators import (
    parse_abstract,
    parse_additional_metadata,
    parse_url,
    split_coverages,
    split_dates,
)
from hsclient.schemas.validators import list_not_empty, parse_identifier, parse_sources


class ResourceMetadata(BaseMetadata):
    type: AnyUrl = Field(const=True, default="CompositeResource", description="TODO Jeff", title="TODO Jeff")

    url: AnyUrl = Field(description="TODO Jeff", title="TODO Jeff")

    identifier: AnyUrl = Field(description="TODO Jeff", title="TODO Jeff")
    title: str = Field(max_length=300, default=None, description="TODO Jeff", title="TODO Jeff")
    abstract: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    language: str = Field(description="TODO Jeff", title="TODO Jeff")
    subjects: List[str] = Field(default=[], description="TODO Jeff", title="TODO Jeff")
    creators: List[Creator] = Field(default=[], description="TODO Jeff", title="TODO Jeff")
    contributors: List[Contributor] = Field(default=[], description="TODO Jeff", title="TODO Jeff")
    sources: List[str] = Field(default=[], description="TODO Jeff", title="TODO Jeff")
    relations: List[Relation] = Field(default=[], description="TODO Jeff", title="TODO Jeff")
    additional_metadata: Dict[str, str] = Field(default={}, description="TODO Jeff", title="TODO Jeff")
    rights: Rights = Field(description="TODO Jeff", title="TODO Jeff")
    created: datetime = Field(default_factory=datetime.now, description="TODO Jeff", title="TODO Jeff")
    modified: datetime = Field(default_factory=datetime.now, description="TODO Jeff", title="TODO Jeff")
    published: datetime = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    awards: List[AwardInfo] = Field(default=[], description="TODO Jeff", title="TODO Jeff")
    spatial_coverage: Union[PointCoverage, BoxCoverage] = Field(
        default=None, description="TODO Jeff", title="TODO Jeff"
    )
    period_coverage: PeriodCoverage = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    publisher: Publisher = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    citation: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")

    _parse_coverages = root_validator(pre=True, allow_reuse=True)(split_coverages)
    _parse_dates = root_validator(pre=True, allow_reuse=True)(split_dates)
    _parse_additional_metadata = root_validator(pre=True, allow_reuse=True)(parse_additional_metadata)
    _parse_abstract = root_validator(pre=True)(parse_abstract)
    _parse_url = root_validator(pre=True, allow_reuse=True)(parse_url)

    _parse_identifier = validator("identifier", pre=True)(parse_identifier)
    _parse_sources = validator("sources", pre=True)(parse_sources)

    _language_constraint = validator('language', allow_reuse=True)(language_constraint)
    _creators_constraint = validator('creators')(list_not_empty)
