from datetime import datetime
from typing import Optional, Union, List

from pydantic import Field

from hsclient.metadata_adapter.legacy_resource_models import Creator as LegacyCreator
from hsclient.metadata_adapter.legacy_resource_models import Contributor as LegacyContributor
from hsclient.schema.base import (
    Contributor,
    Creator,
    Organization,
    MediaType,
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
        json_schema_extra={"readOnly": True},
    )
    dateCreated: datetime = Field(
        title="Date created", description="The date on which the resource was created.",
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
    associatedMedia: Optional[Union[MediaType, List[MediaType]]] = Field(
        title="Resource content",
        description="A media object that encodes this CreativeWork. This property is a synonym for encoding.",
        default=None,
        json_schema_extra={"readOnly": True},
    )
    citation: Optional[List[str]] = Field(
        title="Citation",
        description="A bibliographic citation for the resource.",
        default=None,
        json_schema_extra={"readOnly": True},
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
