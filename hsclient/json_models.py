from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union, Any

from hsmodels.schemas.enums import UserIdentifierType
from pydantic import AnyUrl, BaseModel, HttpUrl, field_validator


class User(BaseModel):
    name: str = None
    email: str = None
    url: AnyUrl = None
    phone: str = None
    address: str = None
    organization: str = None
    website: Optional[HttpUrl] = None
    identifiers: Dict[UserIdentifierType, AnyUrl] = {}
    type: str = None
    subject_areas: List[str] = []
    date_joined: datetime = None

    @field_validator("subject_areas", mode='before')
    def split_subject_areas(cls, value):
        if isinstance(value, str):
            return value.split(", ")
        if value is None:
            return []
        return value

    @field_validator("website", mode='before')
    def handle_empty_website(cls, v):
        if v == "":
            v = None
        return v


class ResourcePreview(BaseModel):
    resource_type: str
    resource_title: str
    resource_id: str
    abstract: Optional[str] = None
    authors: List[str] = []
    creator: str
    doi: Optional[str] = None
    date_created: str
    date_last_updated: str
    public: bool
    discoverable: bool
    shareable: bool
    coverages: Union[List[Dict[str, Any]], List] = []
    immutable: bool
    published: bool
    resource_url: str
    resource_map_url: str
    science_metadata_url: str

    @field_validator("authors", mode='before')
    def handle_null_author(cls, v):
        # return empty list when supplied authors field is None.
        if v is None:
            return []

        # assert iterable non-string
        assert isinstance(v, (Tuple, List))

        # filter to remove all empty x's in v ("", None, or equivalent)
        return list(filter(lambda x: x, v))

    @field_validator("coverages", mode='before')
    def handle_null_coverages(cls, v):
        # return empty list when supplied coverages field is None.
        if v is None:
            return []
        return v
