from datetime import datetime
from enum import Enum
from typing import Any, List, Literal, Optional, Union

from hsmodels.schemas.enums import RelationType
from pydantic import AnyUrl, BaseModel, HttpUrl, TypeAdapter, ValidationError, model_validator

import hsclient.schema.base as schema
from hsclient.schema.core import SchemaBaseModel


class StringEnum(str, Enum):
    pass


url_adapter = TypeAdapter(AnyUrl)


def is_url(value: str) -> bool:
    try:
        url_adapter.validate_python(value)
        return True
    except ValidationError:
        return False


class BasePerson(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    organization: Optional[str] = None
    homepage: Optional[HttpUrl] = None
    address: Optional[str] = None
    identifiers: Optional[dict] = {}

    def to_dataset_person(self, person_type):
        if self.name:
            person = person_type.model_construct()
            person.name = self.name
            if self.email:
                person.email = self.email
            if self.organization:
                affiliation = schema.Organization.model_construct()
                affiliation.name = self.organization
                person.affiliation = affiliation
            _ORCID_identifier = self.identifiers.get("ORCID", "")
            if _ORCID_identifier:
                person.identifier = _ORCID_identifier
        else:
            person = schema.Organization.model_construct()
            person.name = self.organization
            if self.homepage:
                person.url = self.homepage
            if self.address:
                person.address = self.address

        return person


class Creator(BasePerson):
    # TODO: The field 'creator_order' is not part of the schema.org Creator model
    # and our implementation of the schema.org Creator model is yet to support it. Until then,
    # we cannot map it to this legacy Creator model
    # creator_order: Optional[int] = None

    def to_dataset_creator(self):
        return self.to_dataset_person(schema.Creator)


class Contributor(BasePerson):

    def to_dataset_contributor(self):
        return self.to_dataset_person(schema.Contributor)


class Publisher(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None

    def to_dataset_publisher(self):
        publisher = schema.Organization.model_construct()
        publisher.name = self.name
        publisher.url = self.url
        return publisher


class Award(BaseModel):
    funding_agency_name: str
    title: Optional[str] = None
    number: Optional[str] = None
    funding_agency_url: Optional[HttpUrl] = None

    def to_dataset_grant(self):
        grant = schema.Grant.model_construct()
        if self.title:
            grant.name = self.title
        else:
            grant.name = self.funding_agency_name
        if self.number:
            grant.identifier = self.number

        funder = schema.Organization.model_construct()
        funder.name = self.funding_agency_name
        if self.funding_agency_url:
            funder.url = self.funding_agency_url

        grant.funder = funder
        return grant


class TemporalCoverage(BaseModel):
    start: datetime
    end: datetime

    def to_dataset_temporal_coverage(self):
        temp_cov = schema.TemporalCoverage.model_construct()
        if self.start:
            temp_cov.startDate = self.start
            if self.end:
                temp_cov.endDate = self.end
        return temp_cov


class SpatialCoverageBox(BaseModel):
    name: Optional[str] = None
    northlimit: float
    eastlimit: float
    southlimit: float
    westlimit: float
    type: str = "box"
    # TODO: These 2 fields are not supported as there are no matching fields in the
    # schema.org spatial coverage model, but we may have to add them to the schema.org
    # spatial coverage model if we want to preserve the metadata editing api in hsclient
    # units: Optional[str] = None
    # projection: Optional[str] = None

    def to_dataset_spatial_coverage(self):
        place = schema.Place.model_construct()
        if self.name:
            place.name = self.name

        place.geo = schema.GeoShape.model_construct()
        place.geo.box = f"{self.northlimit} {self.eastlimit} {self.southlimit} {self.westlimit}"
        return place


class SpatialCoveragePoint(BaseModel):
    name: Optional[str] = None
    north: float
    east: float
    type: str = "point"
    # TODO: These 2 fields are not supported as there are no matching fields in the schema.org
    # spatial coverage model, but we may have to add them to the schema.org
    # spatial coverage model if we want to preserve the metadata editing api in hsclient
    # units: Optional[str] = None
    # projection: Optional[str] = None

    def to_dataset_spatial_coverage(self):
        place = schema.Place.model_construct()
        if self.name:
            place.name = self.name
        place.geo = schema.GeoCoordinates.model_construct()
        place.geo.latitude = self.north
        place.geo.longitude = self.east
        return place


class Relation(BaseModel):
    type: RelationType
    value: str

    def to_dataset_relation(self):
        relation = schema.Relation.model_construct()
        relation.name = self.type
        return self._to_dataset_relation(relation)

    def _to_dataset_relation(self, relation):
        self.value = self.value.strip()
        if "," in self.value:
            description, url = self.value.rsplit(",", 1)
            relation.description = description.strip()
            url = url.strip()
            if is_url(url):
                relation.url = url
            else:
                relation.description = self.value
        else:
            if is_url(self.value):
                relation.url = self.value
            else:
                relation.description = self.value
        return relation


class Rights(BaseModel):
    statement: Optional[str] = None
    url: Optional[HttpUrl] = None

    def to_dataset_license(self):
        _license = schema.CreativeWork.model_construct()
        _license.name = self.statement
        _license.url = self.url
        return _license


class LegacyResourceMetadata(SchemaBaseModel):
    """This represents legacy metadata model for a HydroShare resource.
    This is used to convert legacy resource metadata to resource metadata in schema.org format
    to write to s3 as user metadata for a resource.
    """

    type: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[HttpUrl] = None
    identifier: Optional[HttpUrl] = None
    creators: List[Creator] = []
    contributors: List[Contributor] = []
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    published: Optional[datetime] = None
    publisher: Optional[Publisher] = None
    subjects: Optional[List[str]] = None
    language: Optional[str] = None
    rights: Optional[Rights] = None
    awards: List[Award] = []
    spatial_coverage: Optional[Union[SpatialCoverageBox, SpatialCoveragePoint]] = None
    period_coverage: Optional[TemporalCoverage] = None
    relations: Optional[List[Relation]] = []

    # 'isPartOf', 'hasPart', and 'provider' are not part of the legacy resource metadata model
    isPartOf: Optional[List[schema.IsPartOf]] = []
    hasPart: Optional[List[schema.HasPart]] = []
    provider: Optional[Union[schema.Organization, schema.Provider]] = None

    citation: Optional[str] = None

    # 'associatedMedia' is not part of the legacy resource metadata model,
    #  but we need it to generate the resource files objects in hsclient Resource model
    associatedMedia: Union[List[Any], Any] = None
    sharing_status: Optional[Literal["private", "public", "published", "discoverable"]] = None
    additional_metadata: Optional[dict] = {}
    extra_columns: Optional[dict] = {}

    _frozen_fields: set = set()

    def freeze_field(self, name: str):
        # Check that it's a valid model field
        if name not in self.__class__.model_fields:
            raise ValueError(f"'{name}' is not a valid field of {self.__class__.__name__}")

        self._frozen_fields.add(name)

    def __setattr__(self, name, value):
        if hasattr(self, "_frozen_fields") and name in self._frozen_fields:
            raise AttributeError(f"Field '{name}' is frozen")
        super().__setattr__(name, value)

    @model_validator(mode="before")
    @classmethod
    def set_extra_columns(cls, data: Any):
        if isinstance(data, dict):
            extra_fields = data.keys() - cls.model_fields.keys()
            if "extra_columns" not in data:
                data["extra_columns"] = {}
            if extra_fields:
                data["extra_columns"].update({field_name: data[field_name] for field_name in extra_fields})
        return data
