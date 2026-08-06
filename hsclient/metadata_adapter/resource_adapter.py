from datetime import datetime
from typing import Optional, Union, List

from pydantic import HttpUrl
from hsclient.metadata_adapter.resource_models import (
    SchemaOrgCreator,
    SchemaOrgContributor,
    SchemaOrgOrganization,
)
from hsclient.metadata_adapter.legacy_resource_models import (
    Rights as LegacyRights,
    Award as LegacyAward,
    Relation as LegacyRelation,
    TemporalCoverage as LegacyPeriodCoverage,
    SpatialCoverageBox as LegacyBoxCoverage,
    SpatialCoveragePoint as LegacyPointCoverage,
    Publisher as LegacyPublisher,
    LegacyResourceMetadata,
)
from hsmodels.schemas.enums import RelationType
from hsclient.schema.base import (
    CreativeWork,
    Grant,
    IsPartOf,
    HasPart,
    LinkedData,
    Place,
    PublisherOrganization,
    PropertyValue,
    Relation,
    SchemaBaseModel,
    TemporalCoverage,
    GeoCoordinates,
    Organization,
    Provider,
    Draft,
    Private,
    Incomplete,
    Obsolete,
    Published,
    Public,
    Discoverable,
    GeoShape,
    MediaType,
)


class ResourceMetadataAdapter(SchemaBaseModel):
    """A pydantic model representing the Schema.org based CoreMetadata for HydroShare resources, 
    with methods to convert to legacy resource metadata models used for metadata editing using hsclient."""
    type: Optional[str] = None
    additionalType: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    identifier: Optional[List[str]] = None
    creator: Optional[List[Union[SchemaOrgCreator, SchemaOrgOrganization]]] = []
    contributor: Optional[List[Union[SchemaOrgContributor, SchemaOrgOrganization]]] = []
    dateCreated: Optional[datetime] = None
    dateModified: Optional[datetime] = None
    datePublished: Optional[datetime] = None
    keywords: Optional[List[str]] = []
    inLanguage: Optional[str] = None
    license: Optional[Union[CreativeWork, HttpUrl]] = None
    funding: Optional[List[Grant]] = []
    relation: Optional[List[Relation]] = []
    associatedMedia: Optional[Union[MediaType, List[MediaType]]] =[]
    isPartOf: Optional[List[IsPartOf]] = []
    hasPart: Optional[List[Union[LinkedData, HasPart]]] = []

    temporalCoverage: Optional[TemporalCoverage] = None
    spatialCoverage: Optional[Place] = None
    publisher: Optional[PublisherOrganization] = None
    additionalProperty: Optional[List[PropertyValue]] = []
    citation: Optional[List[str]] = []
    # No need to convert provider as there is no matching field in the legacy metadata model
    # and it is not allowed for editing using hsclient
    provider: Union[Organization, Provider] = None

    creativeWorkStatus: Optional[Union[Draft, Private, Incomplete, Obsolete, Published, Public, Discoverable]] = None

    def to_legacy_sharing_status(self) -> Optional[str]:
        if self.creativeWorkStatus is None:
            return None
        print(f"Creative work status: {self.creativeWorkStatus}")
        if isinstance(self.creativeWorkStatus, Published):
            return "published"
        elif isinstance(self.creativeWorkStatus, Public):
            return "public"
        elif isinstance(self.creativeWorkStatus, Discoverable):
            return "discoverable"
        return 'private'
    
    def to_legacy_citation(self) -> Optional[str]:
        if not self.citation:
            return None
        return self.citation[0]

    def to_legacy_additional_metadata(self) -> Optional[dict]:
        if not self.additionalProperty:
            return {}

        return {prop.name: prop.value for prop in self.additionalProperty}

    def to_legacy_publisher(self) -> Optional[LegacyPublisher]:
        if not self.publisher:
            return None
        publisher = LegacyPublisher.model_construct()
        publisher.name = self.publisher.name
        if self.publisher.url:
            publisher.url = str(self.publisher.url)
        return publisher

    def to_legacy_spatial_coverage(self) -> Optional[Union[LegacyPointCoverage, LegacyBoxCoverage]]:
        if not self.spatialCoverage or not self.spatialCoverage.geo:
            return None

        geo = self.spatialCoverage.geo
        if isinstance(geo, GeoCoordinates):
            return LegacyPointCoverage.model_construct(
                name=self.spatialCoverage.name,
                north=geo.latitude,
                east=geo.longitude,
                type="point",
            )
        elif isinstance(geo, GeoShape):
            northlimit, eastlimit, southlimit, westlimit = None, None, None, None
            try:
                northlimit, eastlimit, southlimit, westlimit = map(float, geo.box.split())
            except Exception as e:
                print(f"Error parsing geo.box string: {geo.box}, error: {e}")
                return None

            return LegacyBoxCoverage.model_construct(
                name=self.spatialCoverage.name,
                northlimit=northlimit,
                eastlimit=eastlimit,
                southlimit=southlimit,
                westlimit=westlimit,
                type="box",
            )
        else:
            return None
    
    def to_legacy_temporal_coverage(self) -> Optional[LegacyPeriodCoverage]:
        if not self.temporalCoverage:
            return None
        legacy_period = LegacyPeriodCoverage.model_construct()
        legacy_period.start = self.temporalCoverage.startDate
        if self.temporalCoverage.endDate:
            legacy_period.end = self.temporalCoverage.endDate
        return legacy_period

    def to_legacy_relations(self) -> Optional[List[LegacyRelation]]:
        if not self.relation:
            return []
        legacy_relations = []
        for relation in self.relation:
            if type(relation) in (IsPartOf, HasPart):
                continue
            legacy_relation = LegacyRelation.model_construct()
            relation_type = _to_legacy_relation_type(relation.name)
            if relation_type is None:
                print(f"Warning: Could not convert relation name '{relation.name}' to legacy relation type")
                continue
            legacy_relation.type = relation_type
            legacy_relation.value = _build_relation_value(relation.description, relation.url)
            legacy_relations.append(legacy_relation)
        return legacy_relations

    def to_legacy_award(self) -> Optional[List[LegacyAward]]:
        if not self.funding:
            return []
        awards = []
        for grant in self.funding:
            award = LegacyAward.model_construct()
            award.title = grant.name
            if grant.identifier:
                award.number = grant.identifier
            if grant.funder and grant.funder.name:
                award.funding_agency_name = grant.funder.name
                if grant.funder.url:
                    award.funding_agency_url = str(grant.funder.url)
            awards.append(award)
        return awards

    def to_legacy_rights(self) -> Optional[LegacyRights]:
        if self.license is None:
            return None
        if not isinstance(self.license, CreativeWork):
            return LegacyRights(url=str(self.license))
        return LegacyRights(statement=self.license.name, url=str(self.license.url) if self.license.url else None)

    def to_legacy_resource_metadata(self) -> LegacyResourceMetadata:
        legacy_metadata = LegacyResourceMetadata.model_construct()
        legacy_metadata.type = self.additionalType
        legacy_metadata.title = self.name
        legacy_metadata.abstract = self.description
        legacy_metadata.url = self.url
        if self.identifier:
            legacy_metadata.identifier = self.identifier[0]
        legacy_metadata.creators = [creator.to_legacy_creator() for creator in self.creator or []]
        legacy_metadata.contributors = [contributor.to_legacy_contributor() for contributor in self.contributor or []]
        legacy_metadata.created = self.dateCreated
        legacy_metadata.modified = self.dateModified
        legacy_metadata.published = self.datePublished
        legacy_metadata.subjects = self.keywords
        legacy_metadata.language = self.inLanguage
        legacy_metadata.rights = self.to_legacy_rights()
        legacy_metadata.awards = self.to_legacy_award()
        legacy_metadata.spatial_coverage = self.to_legacy_spatial_coverage()
        legacy_metadata.period_coverage = self.to_legacy_temporal_coverage()
        legacy_metadata.relations = self.to_legacy_relations()
        # The legacy model originally doesnot have hasPart, isPartOf, and provider fields,
        # we are providing them here for completeness so that they can be accessed in hsclient,
        # - no conversion is needed from schemaorg to legacy for these fields
        legacy_metadata.hasPart = self.hasPart
        legacy_metadata.isPartOf = self.isPartOf
        legacy_metadata.provider = self.provider

        legacy_metadata.citation = self.to_legacy_citation()
        legacy_metadata.additional_metadata = self.to_legacy_additional_metadata()
        legacy_metadata.associatedMedia = self.associatedMedia
        legacy_metadata.publisher = self.to_legacy_publisher()
        legacy_metadata.sharing_status = self.to_legacy_sharing_status()
        # set the frozen fields so that these fields can't be edited using hsclient
        for field in [
            "type",
            "url",
            "created",
            "modified",
            "published",
            "publisher",
            "identifier",
            "sharing_status",
            "citation",
            'provider',
            'hasPart',
            "associatedMedia",
        ]:
            legacy_metadata.freeze_field(field)

        return legacy_metadata

def _build_relation_value(description: Optional[str], url: Optional[str]) -> str:
    description = (description or "").strip()
    url = (str(url) if url else "").strip()
    if description and url:
        return f"{description}, {url}"
    return description or url


def _to_legacy_relation_type(relation_name: Optional[str]) -> Optional[RelationType]:
    if not relation_name:
        return None
    try:
        return RelationType[relation_name]
    except KeyError:
        pass

    normalized_name = relation_name.replace(" ", "").lower()
    for relation_type in RelationType:
        if relation_type.name.lower() == normalized_name:
            return relation_type
        if relation_type.value.lower() == relation_name.lower():
            return relation_type
    return None
