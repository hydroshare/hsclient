from datetime import datetime
from typing import Dict, List, Tuple

from hsmodels.schemas.enums import UserIdentifierType
from pydantic import AnyUrl, BaseModel, validator


class User(BaseModel):
    name: str = None
    email: str = None
    url: AnyUrl = None
    phone: str = None
    address: str = None
    organization: str = None
    website: str = None
    identifiers: Dict[UserIdentifierType, str] = {}
    type: str = None
    subject_areas: List[str] = []
    date_joined: datetime = None

    @validator("subject_areas", pre=True)
    def split_subject_areas(cls, value):
        return value.split(", ") if value else []


class ResourcePreview(BaseModel):
    resource_type: str = None
    resource_title: str = None
    resource_id: str = None
    abstract: str = None
    authors: List[str] = []
    creator: str = None
    doi: str = None
    date_created: str = None
    date_last_updated: str = None
    public: bool = None
    discoverable: bool = None
    shareable: bool = None
    coverages: Dict[str, str] = None
    immutable: bool = None
    published: bool = None
    resource_url: str = None
    resource_map_url: str = None
    resource_metadata_url: str = None

    @validator("authors", pre=True)
    def handle_null_author(cls, v):
        # return empty list when supplied authors field is None.
        if v is None:
            return []

        # assert iterable non-string
        assert isinstance(v, (Tuple, List))

        # filter to remove all empty x's in v ("", None, or equivalent)
        return list(filter(lambda x: x, v))
