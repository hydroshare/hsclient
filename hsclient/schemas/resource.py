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
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: AnyUrl = Field(const=True, default="CompositeResource", title="TODO Jeff", description="TODO Jeff")

    url: AnyUrl = Field(title="TODO Jeff", description="TODO Jeff")

    identifier: AnyUrl = Field(title="TODO Jeff", description="TODO Jeff")
    title: str = Field(max_length=300, default=None, title="TODO Jeff", description="TODO Jeff")
    abstract: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    language: str = Field(title="TODO Jeff", description="TODO Jeff")
    subjects: List[str] = Field(default=[], title="TODO Jeff", description="TODO Jeff")
    creators: List[Creator] = Field(default=[], title="TODO Jeff", description="TODO Jeff")
    contributors: List[Contributor] = Field(default=[], title="TODO Jeff", description="TODO Jeff")
    sources: List[str] = Field(default=[], title="TODO Jeff", description="TODO Jeff")
    relations: List[Relation] = Field(default=[], title="TODO Jeff", description="TODO Jeff")
    additional_metadata: Dict[str, str] = Field(default={}, title="TODO Jeff", description="TODO Jeff")
    rights: Rights = Field(title="TODO Jeff", description="TODO Jeff")
    created: datetime = Field(default_factory=datetime.now, title="TODO Jeff", description="TODO Jeff")
    modified: datetime = Field(default_factory=datetime.now, title="TODO Jeff", description="TODO Jeff")
    published: datetime = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    awards: List[AwardInfo] = Field(default=[], title="TODO Jeff", description="TODO Jeff")
    spatial_coverage: Union[PointCoverage, BoxCoverage] = Field(
        default=None, title="TODO Jeff", description="TODO Jeff"
    )
    period_coverage: PeriodCoverage = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    publisher: Publisher = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    citation: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")

    _parse_coverages = root_validator(pre=True, allow_reuse=True)(split_coverages)
    _parse_dates = root_validator(pre=True, allow_reuse=True)(split_dates)
    _parse_additional_metadata = root_validator(pre=True, allow_reuse=True)(parse_additional_metadata)
    _parse_abstract = root_validator(pre=True)(parse_abstract)
    _parse_url = root_validator(pre=True, allow_reuse=True)(parse_url)

    _parse_identifier = validator("identifier", pre=True)(parse_identifier)
    _parse_sources = validator("sources", pre=True)(parse_sources)

    _language_constraint = validator('language', allow_reuse=True)(language_constraint)
    _creators_constraint = validator('creators')(list_not_empty)
