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
    A class used to represent the metadata for a resource
    """

    class Config:
        title = 'Resource Metadata'

    type: AnyUrl = Field(const=True, default="CompositeResource", title="Resource Type", description="An object containing a URL that points to the HydroShare resource type selected from the hsterms namespace")

    url: AnyUrl = Field(title="URL", description="An object containing the URL for a resource")

    identifier: AnyUrl = Field(title="Identifier", description="An object containing the URL-encoded unique identifier for a resource")
    title: str = Field(max_length=300, default=None, title="Title", description="A string containing the name given to a resource")
    abstract: str = Field(default=None, title="Abstract", description="A string containing a summary of a resource")
    language: str = Field(title="Language", description="A 3-character string for the language in which the metadata and content of a resource are expressed")
    subjects: List[str] = Field(default=[], title="Subject keywords", description="A list of keyword strings expressing the topic of a resource")
    creators: List[Creator] = Field(default=[], title="Creators", description="A list of Creator objects indicating the entities responsible for creating a resource")
    contributors: List[Contributor] = Field(default=[], title="Contributors", description="A list of Contributor objects indicating the entities that contributed to a resource")
    sources: List[str] = Field(default=[], title="Sources", description="A list of strings containing references to related resources from which a described resource was derived")
    relations: List[Relation] = Field(default=[], title="Related resources", description="A list of Relation objects representing resources related to a described resource")
    additional_metadata: Dict[str, str] = Field(default={}, title="Additional metadata", description="A dictionary containing key-value pair metadata associated with a resource")
    rights: Rights = Field(title="Rights", description="An object congaining information about rights held in an over a resource")
    created: datetime = Field(default_factory=datetime.now, title="Creation date", description="A datetime object containing the instant associated with when a resource was created")
    modified: datetime = Field(default_factory=datetime.now, title="Modified date", description="A datetime object containing the instant associated with when a resource was last modified")
    published: datetime = Field(default=None, title="Published date", description="A datetime object containing the instant associated with when a resource was published")
    awards: List[AwardInfo] = Field(default=[], title="Funding agency information", description="A list of objects containing information about the funding agencies and awards associated with a resource")
    spatial_coverage: Union[PointCoverage, BoxCoverage] = Field(
        default=None, title="Spatial coverage", description="An object containing information about the spatial topic of a resource, the spatial applicability of a resource, or jurisdiction under with a resource is relevant"
    )
    period_coverage: PeriodCoverage = Field(default=None, title="Temporal coverage", description="An object containing information about the temporal topic or applicability of a resource")
    publisher: Publisher = Field(default=None, title="Publisher", description="An object containing information about the publisher of a resource")
    citation: str = Field(default=None, title="Citation", description="A string containing the biblilographic citation for a resource")

    _parse_coverages = root_validator(pre=True, allow_reuse=True)(split_coverages)
    _parse_dates = root_validator(pre=True, allow_reuse=True)(split_dates)
    _parse_additional_metadata = root_validator(pre=True, allow_reuse=True)(parse_additional_metadata)
    _parse_abstract = root_validator(pre=True)(parse_abstract)
    _parse_url = root_validator(pre=True, allow_reuse=True)(parse_url)

    _parse_identifier = validator("identifier", pre=True)(parse_identifier)
    _parse_sources = validator("sources", pre=True)(parse_sources)

    _language_constraint = validator('language', allow_reuse=True)(language_constraint)
    _creators_constraint = validator('creators')(list_not_empty)
