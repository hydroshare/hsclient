from typing import List, Optional, Union


from pydantic import (
    Field,
    HttpUrl,
)

from .base import (
    SchemaBaseModel,
    TemporalCoverage,
    Place,
    HasPart,
    IsPartOf,
    Relation,
    MediaType,
    PropertyValue,
)


class CoreMetadata(SchemaBaseModel):

    ###################
    # REQUIRED FIELDS #
    ###################
    context: HttpUrl = Field(
        alias="@context",  # type: ignore
        default=HttpUrl(
            "https://hydroshare.org/schema"
        ),  # TODO: This is a placeholder for now.
        description="Specifies the vocabulary employed for understanding the structured data markup.",
    )
    type: str = Field(
        alias="@type",  # type: ignore
        default="CreativeWork",
        description="A creative work that may include various forms of content, such as datasets,"
        " software source code, digital documents, etc.",
        frozen=True,
        json_schema_extra={"readOnly": True},
        #        json_schema_extra={
        #            "enum": ["Dataset", "Notebook", "Software Source Code"],
        #        },
    )
    additionalType: Optional[str] = Field(
        title="Additional type",
        description="An additional type for the resource. This can be used to further specify the type of the"
                    " resource (e.g., Composite Resource).",
        frozen=True,
        json_schema_extra={"readOnly": True},
    )
    name: str = Field(
        title="Name or title",
        description="A text string with a descriptive name or title for the resource.",
    )
    description: Optional[str] = Field(
        default=None,
        title="Description or abstract",
        description="A text string containing a description/abstract for the resource.",
    )
    keywords: Optional[List[str]] = Field(
        min_length=1,
        description="Keywords or tags used to describe the dataset, delimited by commas.",
        default=[],
    )

    ###################
    # OPTIONAL FIELDS #
    ###################    
    temporalCoverage: Optional[TemporalCoverage] = Field(
        title="Temporal coverage",
        description="The time period that applies to all of the content within the resource.",
        default=None,
    )
    spatialCoverage: Optional[Place] = Field(
        description="The spatialCoverage of a CreativeWork indicates the place(s) which are the focus of the content. "
        "It is a sub property of contentLocation intended primarily for more technical and "
        "detailed materials. For example with a Dataset, it indicates areas that the dataset "
        "describes: a dataset of New York weather would have spatialCoverage which was the "
        "place: the state of New York.",
        default=None,
    )
    hasPart: Optional[List[HasPart]] = Field(
        title="Has part",
        description="Link to or citation for a related resource that is part of this resource.",
        default=None,
    )
    isPartOf: Optional[List[IsPartOf]] = Field(
        title="Is part of",
        description="Link to or citation for a related resource that this resource is a "
        "part of - e.g., a related collection.",
        default=None,
    )
    # 'relation' is not a standard schema.org property, but we include it here to 
    # capture any other types of relations that don't fit into the above properties 
    relation: Optional[List[Relation]] = Field(
        title="Relation",
        description="All other types of relations",
        default=None,
    )
    additionalProperty: Optional[List[PropertyValue]] = Field(
        title="Additional properties",
        default=None,
        description="Additional properties of the place.",
    )

    # using MediaType here to allow for MediaObject and its subclasses (e.g., DataDownload, VideoObject)
    associatedMedia: Optional[Union[MediaType, List[MediaType]]] = Field(
        title="Resource content",
        description="A media object that encodes this CreativeWork. This property is a synonym for encoding.",
        default=None,
        frozen=True,
        json_schema_extra={"readOnly": True},
    )
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            HttpUrl: str,  # Convert HttpUrl to a string during serialization
        },
    }
