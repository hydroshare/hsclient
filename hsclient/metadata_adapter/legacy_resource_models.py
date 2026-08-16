from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

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
    # TODO: make this a required field
    creator_order: Optional[int] = None

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


class AwardInfo(BaseModel):
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
    # original: hsmodels.schemas.fields.PeriodCoverage
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
    # original: hsmodels.schemas.fields.BoxCoverage
    name: Optional[str] = None
    northlimit: float
    eastlimit: float
    southlimit: float
    westlimit: float
    type: str = "box"
    projection: Optional[str] = None
    # TODO: 'units' is not supported as there is no matching field in the schema.org spatial
    # coverage model. In original BoxCoverage model, 'units' is a required field.
    # units: Optional[str] = None

    def to_dataset_spatial_coverage(self):
        place = schema.Place.model_construct()
        if self.name:
            place.name = self.name

        place.geo = schema.GeoShape.model_construct()
        # Resource-level box token order is "N E S W", matching HydroShare's own schema.org
        # generator (hs_core/hydroshare_schemaorg_adapter.py) -- not the "S W N E" order used by
        # the aggregation-level raster/netcdf extractors.
        place.geo.box = f"{self.northlimit} {self.eastlimit} {self.southlimit} {self.westlimit}"
        if self.projection:
            # Resource-level coverage coordinates are always decimal degrees in HydroShare, so
            # srsType is always "geographic" -- there is no legacy field to round-trip it from.
            place.srs = schema.SpatialReference(name=self.projection, srsType="geographic")
        return place


class SpatialCoveragePoint(BaseModel):
    # original: hsmodels.schemas.fields.PointCoverage
    name: Optional[str] = None
    north: float
    east: float
    type: str = "point"
    projection: Optional[str] = None
    # TODO: 'units' is not supported as there is no matching field in the schema.org spatial
    # coverage model. In original PointCoverage model 'units' is a required field.
    # units: Optional[str] = None

    def to_dataset_spatial_coverage(self):
        place = schema.Place.model_construct()
        if self.name:
            place.name = self.name
        place.geo = schema.GeoCoordinates.model_construct()
        place.geo.latitude = self.north
        place.geo.longitude = self.east
        if self.projection:
            # Resource-level coverage coordinates are always decimal degrees in HydroShare, so
            # srsType is always "geographic" -- there is no legacy field to round-trip it from.
            place.srs = schema.SpatialReference(name=self.projection, srsType="geographic")
        return place


class Relation(BaseModel):
    type: RelationType
    value: str

    def to_dataset_relation(self):
        if self.type == RelationType.isPartOf:
            relation = schema.IsPartOf.construct()
        elif self.type == RelationType.hasPart:
            relation = schema.HasPart.construct()
        else:
            relation = schema.Relation.construct()
            relation.name = self.type.name

        if ',' in self.value:
            description, url = self.value.rsplit(',', 1)
        else:
            description, url = self.value, ""
        if not description:
            description = ""
        if not url:
            url = ""
        url_str = url.strip()
        relation.description = description.strip()
        parsed_url = None
        if url_str:
            try:
                parsed_url = HttpUrl(url_str)
            except Exception:
                # url_str is not a valid URL — treat as part of the description
                relation.description = f"{relation.description}, {url_str}".strip(", ")
        relation.url = parsed_url
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
    contributors: Optional[List[Contributor]] = []
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    published: Optional[datetime] = None
    publisher: Optional[Publisher] = None
    subjects: Optional[List[str]] = []
    language: Optional[str] = None
    rights: Optional[Rights] = None
    awards: Optional[List[AwardInfo]] = []
    spatial_coverage: Optional[Union[SpatialCoverageBox, SpatialCoveragePoint]] = None
    period_coverage: Optional[TemporalCoverage] = None
    relations: Optional[List[Relation]] = []

    # 'provider', 'version', and 'subjectOf' are not part of the legacy
    # resource metadata model - added here for completeness with schema.org resource metadata model.
    provider: Optional[Union[schema.Organization, schema.Provider]] = None
    version: Optional[str] = None
    subjectOf: Optional[List[schema.SubjectOf]] = []

    citation: Optional[str] = None

    # 'associatedMedia' is not part of the legacy resource metadata model,
    #  but we need it to generate the resource files objects in hsclient Resource model
    associatedMedia: Union[List[Any], Any] = None

    # 'sharing_status' is not part of the legacy resource metadata model
    # - added here for completeness with schema.org resource metadata model.
    sharing_status: Optional[Literal["private", "public", "published", "discoverable", "draft", "incomplete", "obsolete"]] = None
    additional_metadata: Dict[str, str] = {}

    # Read-only capture of schema.org fields with no dedicated model field, so Resource.save()
    # doesn't silently drop them: S3 has no partial write, so hsclient's JSON becomes the entire
    # new content of user_metadata.json. Fields like viewCount live only there (unlike
    # metadata items, which HydroShare re-merges from system_metadata.json
    # on every read), so anything not captured and replayed here is lost on the next save.
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
