from datetime import datetime
from typing import List, Optional, Union

from pydantic import Field, HttpUrl

from hsclient.metadata_adapter.legacy_resource_models import Contributor as LegacyContributor, Creator as LegacyCreator
from hsclient.schema.base import (
    Contributor,
    CreativeWork,
    Creator,
    Discoverable,
    Draft,
    Grant,
    Incomplete,
    InLanguageStr,
    LanguageEnum,
    MediaType,
    Obsolete,
    Organization,
    Private,
    Provider,
    Public,
    Published,
    PublisherOrganization,
    SubjectOf,
)
from hsclient.schema.core import CoreMetadata


class SchemaOrgResourceMetadata(CoreMetadata):
    # This class overrides the CoreMetadata frozen fields for the adapter to work
    type: str = Field(
        alias="@type",  # type: ignore
        default="CreativeWork",
        description="A creative work that may include various forms of content, such as datasets,"
        " software source code, digital documents, etc.",
        json_schema_extra={"readOnly": True},
    )
    additionalType: Optional[str] = Field(
        title="Additional type",
        description="An additional type for the resource. This can be used to further specify the type of the"
        " resource (e.g., Composite Resource).",
    )
    dateCreated: datetime = Field(
        title="Date created",
        description="The date on which the resource was created.",
        json_schema_extra={"readOnly": True},
    )
    datePublished: Optional[datetime] = Field(
        title="Date published",
        description="Date of first publication for the resource.",
        default=None,
        json_schema_extra={"readOnly": True},
    )
    dateModified: Optional[datetime] = Field(
        title="Date modified",
        description="The date on which the resource was most recently modified or updated.",
        default=None,
        json_schema_extra={"readOnly": True},
    )
    citation: Optional[List[str]] = Field(
        title="Citation",
        description="A bibliographic citation for the resource.",
        default=[],
        json_schema_extra={"readOnly": True},
    )
    url: HttpUrl = Field(
        title="URL",
        description="A URL for the landing page that describes the resource and where the content "
        "of the resource can be accessed. If there is no landing page,"
        " provide the URL of the content.",
    )
    identifier: List[str] = Field(
        title="Identifiers",
        description="Any kind of identifier for the resource. Identifiers may be DOIs or unique strings "
        "assigned by a repository. Multiple identifiers can be entered. Where identifiers can be "
        "encoded as URLs, enter URLs here.",
    )
    creator: List[Union[Creator, Organization]] = Field(description="Person or Organization that created the resource.")
    contributor: Optional[List[Union[Contributor, Organization]]] = Field(
        description="Person or Organization that contributed to the resource.", default=[]
    )
    publisher: Optional[PublisherOrganization] = Field(
        title="Publisher",
        description="Where the resource is permanently published, indicated the repository, service provider,"
        " or organization that published the resource - e.g., CUAHSI HydroShare."
        " This may be the same as Provider.",
        default=None,
    )
    subjectOf: Optional[List[SubjectOf]] = Field(
        title="Subject of",
        description="Link to or citation for a related resource that is about or describes this resource"
        " - e.g., a journal paper that describes this resource or a related metadata document "
        "describing the resource.",
        default=[],
    )
    version: Optional[str] = Field(
        description="A text string indicating the version of the resource.",
        default=None,
    )  # TODO find something better than float for number
    inLanguage: Optional[Union[LanguageEnum, InLanguageStr]] = Field(
        title="Language",
        description="The language of the content of the resource.",
        default=None,
    )
    creativeWorkStatus: Optional[Union[Draft, Incomplete, Obsolete, Published, Public, Discoverable, Private]] = Field(
        title="Resource status",
        description="The status of this resource in terms of its stage in a lifecycle. "
        "Example terms include Incomplete, Draft, Published, and Obsolete.",
        default=None,
    )
    license: Union[CreativeWork, HttpUrl] = Field(description="A license document that applies to the resource.")
    provider: Union[Organization, Provider] = Field(
        description="The repository, service provider, organization, person, or service performer that provides"
        " access to the resource."
    )
    funding: Optional[List[Grant]] = Field(
        description="A Grant or monetary assistance that directly or indirectly provided funding or sponsorship "
        "for creation of the resource.",
        default=[],
    )
    # using MediaType here to allow for MediaObject and its subclasses (e.g., DataDownload, VideoObject)
    associatedMedia: Optional[Union[MediaType, List[MediaType]]] = Field(
        title="Resource content",
        description="A media object that encodes this CreativeWork. This property is a synonym for encoding.",
        default=None,
    )


class SchemaOrgOrganization(Organization):

    def to_legacy_creator(self) -> LegacyCreator:
        creator = LegacyCreator.model_construct()
        creator.organization = self.name
        if self.url:
            creator.homepage = str(self.url)
        if self.address:
            creator.address = self.address
        return creator

    def to_legacy_contributor(self) -> LegacyContributor:
        contributor = LegacyContributor.model_construct()
        contributor.organization = self.name
        if self.url:
            contributor.homepage = str(self.url)
        if self.address:
            contributor.address = self.address
        return contributor


class SchemaOrgCreator(Creator):

    def to_legacy_creator(self) -> LegacyCreator:
        creator = LegacyCreator.model_construct()
        creator.name = self.name
        creator.email = self.email
        if self.identifier:
            orcid = _normalize_orcid(str(self.identifier))
            if orcid:
                creator.identifiers = {"ORCID": orcid}
        if self.affiliation:
            creator.organization = self.affiliation.name

        return creator


class SchemaOrgContributor(Contributor):

    def to_legacy_contributor(self) -> LegacyContributor:
        contributor = LegacyContributor.model_construct()
        contributor.name = self.name
        contributor.email = self.email
        if self.identifier:
            orcid = _normalize_orcid(str(self.identifier))
            if orcid:
                contributor.identifiers = {"ORCID": orcid}
        if self.affiliation:
            contributor.organization = self.affiliation.name
        return contributor


def _normalize_orcid(orcid: Optional[str]) -> Optional[str]:
    if not orcid:
        return None
    orcid = str(orcid).strip()
    if orcid.startswith("http://orcid.org/") or orcid.startswith("https://orcid.org/"):
        return str(orcid)
    return None
