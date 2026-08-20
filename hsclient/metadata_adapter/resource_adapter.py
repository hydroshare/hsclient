from datetime import datetime
from typing import List, Optional, Union

from hsmodels.schemas.enums import RelationType
from pydantic import HttpUrl

from hsclient.metadata_adapter.legacy_resource_models import (
    AwardInfo as LegacyAward,
    LegacyResourceMetadata,
    Publisher as LegacyPublisher,
    Relation as LegacyRelation,
    Rights as LegacyRights,
    SpatialCoverageBox as LegacyBoxCoverage,
    SpatialCoveragePoint as LegacyPointCoverage,
    TemporalCoverage as LegacyPeriodCoverage,
)
from hsclient.metadata_adapter.resource_models import SchemaOrgContributor, SchemaOrgCreator, SchemaOrgOrganization
from hsclient.schema.base import (
    CreativeWork,
    Discoverable,
    Draft,
    GeoCoordinates,
    GeoShape,
    Grant,
    HasPart,
    Incomplete,
    IsPartOf,
    LinkedData,
    MediaType,
    Obsolete,
    Organization,
    Place,
    Private,
    PropertyValue,
    Provider,
    Public,
    Published,
    PublisherOrganization,
    Relation,
    SchemaBaseModel,
    SubjectOf,
    TemporalCoverage,
)


class ResourceMetadataAdapter(SchemaBaseModel):
    """A pydantic model representing the Schema.org based metadata for HydroShare resources,
    with methods to convert to legacy resource metadata models used for metadata editing using hsclient."""

    # Preserve schema.org fields this model doesn't declare (rather than the inherited
    # extra="ignore" silently discarding them) so they survive into extra_columns below
    # instead of being lost.
    model_config = {"extra": "allow"}

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
    associatedMedia: Optional[Union[MediaType, List[MediaType]]] = []
    isPartOf: Optional[List[IsPartOf]] = []
    hasPart: Optional[List[Union[LinkedData, HasPart]]] = []
    version: Optional[str] = None
    temporalCoverage: Optional[TemporalCoverage] = None
    spatialCoverage: Optional[Place] = None
    publisher: Optional[PublisherOrganization] = None
    # TODO: it should be set to : Union[str, List[str], PropertyValue, List[PropertyValue]]
    additionalProperty: Optional[List[PropertyValue]] = []
    citation: Optional[List[str]] = []
    provider: Union[Organization, Provider] = None
    creativeWorkStatus: Optional[Union[Draft, Private, Incomplete, Obsolete, Published, Public, Discoverable]] = None
    subjectOf: Optional[List[SubjectOf]] = []

    def to_legacy_sharing_status(self) -> Optional[str]:
        if self.creativeWorkStatus is None:
            return None
        if isinstance(self.creativeWorkStatus, Published):
            return "published"
        elif isinstance(self.creativeWorkStatus, Public):
            return "public"
        elif isinstance(self.creativeWorkStatus, Discoverable):
            return "discoverable"
        elif isinstance(self.creativeWorkStatus, Draft):
            return "draft"
        elif isinstance(self.creativeWorkStatus, Incomplete):
            return "incomplete"
        elif isinstance(self.creativeWorkStatus, Obsolete):
            return "obsolete"
        elif isinstance(self.creativeWorkStatus, Private):
            return "private"
        else:
            raise ValueError(f"Unknown creativeWorkStatus: {self.creativeWorkStatus}")

    def to_legacy_citation(self) -> Optional[str]:
        if not self.citation:
            return None
        return self.citation[0]

    # TODO: This conversion won't work (causes data loss) as the data formats at each end is different - so remove it
    # add 'additionalProperty' to the legacy model and 'additional_metadata' to the schema model 
    # so we don't need to convert between them.
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

        srs = self.spatialCoverage.srs
        projection = srs.name if srs else None

        geo = self.spatialCoverage.geo
        if isinstance(geo, GeoCoordinates):
            return LegacyPointCoverage.model_construct(
                name=self.spatialCoverage.name,
                north=geo.latitude,
                east=geo.longitude,
                type="point",
                projection=projection,
            )
        elif isinstance(geo, GeoShape):
            # Resource-level box token order is "N E S W" as in HydroShare's schema.org generator.
            try:
                northlimit, eastlimit, southlimit, westlimit = map(float, geo.box.split())
            except Exception as e:
                raise ValueError(f"Invalid geo.box string: {geo.box}, error: {str(e)}")

            return LegacyBoxCoverage.model_construct(
                name=self.spatialCoverage.name,
                northlimit=northlimit,
                eastlimit=eastlimit,
                southlimit=southlimit,
                westlimit=westlimit,
                type="box",
                projection=projection,
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
        # The legacy model has a single 'relations' field -- 'isPartOf', 'hasPart', and 'relation'
        # (schema.org's three separate fields) all collapse back into it here, tagged by
        # RelationType so the legacy<->schema.org round trip is lossless.
        legacy_relations = []

        for is_part_of in self.isPartOf or []:
            legacy_relation = LegacyRelation.model_construct()
            legacy_relation.type = RelationType.isPartOf
            # legacy relation values have no separate title field, so fall back to name
            # when description isn't set
            legacy_relation.value = _build_relation_value(is_part_of.description or is_part_of.name, is_part_of.url)
            legacy_relations.append(legacy_relation)

        for has_part in self.hasPart or []:
            legacy_relation = LegacyRelation.model_construct()
            legacy_relation.type = RelationType.hasPart
            if isinstance(has_part, LinkedData):
                legacy_relation.value = str(has_part.id)
            else:
                legacy_relation.value = _build_relation_value(has_part.description or has_part.name, has_part.url)
            legacy_relations.append(legacy_relation)

        for relation in self.relation or []:
            legacy_relation = LegacyRelation.model_construct()
            relation_type = _to_legacy_relation_type(relation.name)
            if relation_type is None:
                raise ValueError(f"Could not convert relation name '{relation.name}' to legacy relation type")
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
            # type mismatch: legacy_metadata.identifier is a HttpUrl, while self.identifier is a list of strings
            # It seems the schema side identifier list always has only one item - url to the resource landing page
            legacy_metadata.identifier = self.identifier[0]
        legacy_metadata.creators = []
        for order, creator in enumerate(self.creator or [], start=1):
            legacy_creator = creator.to_legacy_creator()
            legacy_creator.creator_order = order
            legacy_metadata.creators.append(legacy_creator)
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
        legacy_metadata.provider = self.provider
        legacy_metadata.version = self.version
        legacy_metadata.subjectOf = self.subjectOf

        legacy_metadata.citation = self.to_legacy_citation()
        # TODO: This conversion won't work (causes data loss) as the data formats at each end is different.
        # Consider adding 'additionalProperty' to the legacy model and 'additional_metadata' to the schema model.
        legacy_metadata.additional_metadata = self.to_legacy_additional_metadata()

        legacy_metadata.associatedMedia = self.associatedMedia
        legacy_metadata.publisher = self.to_legacy_publisher()
        legacy_metadata.sharing_status = self.to_legacy_sharing_status()

        # Preserve any schema.org field this adapter doesn't declare a named field for (captured
        # into self.model_extra via extra="allow" above) so it survives the round trip instead of
        # being silently dropped. model_construct() bypasses LegacyResourceMetadata's own
        # set_extra_columns validator, so it's set explicitly here.
        legacy_metadata.extra_columns = dict(self.model_extra or {})

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
            'version',
            'subjectOf',
            "associatedMedia",
            # extra_columns is a passive capture of whatever hsclient doesn't otherwise model
            # (see above) -- not a field users are meant to add arbitrary metadata through.
            # Frozen so it can't be accidentally cleared/overwritten and silently drop data
            # (e.g. HydroShare system fields like viewCount).
            'extra_columns',
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
    relation_name = relation_name.strip()
    try:
        return RelationType[relation_name]
    except KeyError:
        pass
    for relation_type in RelationType:
        if relation_type.name.lower() == relation_name.lower():
            return relation_type
    for relation_type in RelationType:
        if relation_type.value.lower() == relation_name.lower():
            return relation_type
    return None
