from enum import Enum
from typing import List, Literal, Optional, Union

from pydantic import Field, HttpUrl

from .base import DataCatalog, MediaType, Organization, PropertyValue
from .core import CoreMetadata
from .datavariable import DataVariable, Dimension


class AdditionalType(str, Enum):
    GEOGRAPHIC_FEATURE = 'GeographicFeature'
    GEOGRAPHIC_RASTER = 'GeographicRaster'
    MULTIDIMENSIONAL = 'MultiDimensional'
    TABULAR = 'Tabular'
    SINGLE_FILE = 'GenericFile'
    FILE_SET = 'FileSet'


class ScientificDataset(CoreMetadata):
    """
    A generic dataset extends the CoreMetadata class with a few additional fields and is designed to capture
    scientific file-level (aggregation/content-type) metadata. It also overrides many of the required
    CoreMetadata fields to make them optional. It generally follows the design of the Schema.org Dataset class.
    Used for metadata representation of content types (aggregations).
    TODO: This class needs to be part of hsmodels so that both hydroshare and hsclient can share it.
    """

    context: HttpUrl = Field(
        alias="@context",  # type: ignore
        default=HttpUrl("https://hydroshare.org/schema"),  # TODO: This is a placeholder for now.
        description="Specifies the vocabulary employed for understanding the structured data markup.",
    )
    type: Literal["ScientificDataset"] = Field(
        alias="@type",  # type: ignore
        default="ScientificDataset",
        description="A body of structured information describing some topic(s) of interest.",
        frozen=True,
        json_schema_extra={"readOnly": True},
    )
    additionalType: AdditionalType = Field(
        title="Additional type",
        description="An additional type for the dataset. This can be used to further specify the type of the"
        " dataset (e.g., MultiDimensional).",
        frozen=True,
        json_schema_extra={"readOnly": True},
    )
    variableMeasured: Optional[List[Union[str, PropertyValue, DataVariable]]] = Field(
        title="Variables measured",
        description="Measured variables.",
        default=[],
    )
    dimensions: Optional[List[Dimension]] = Field(
        title="Dimensions",
        description="Dimensions defined in the time series dataset.",
        default=[],
    )
    # redefine associatedMedia from "Core" as a required field
    associatedMedia: Union[MediaType, List[MediaType]] = Field(
        title="Resource content",
        description="A media object that encodes this CreativeWork. This property is a synonym for encoding.",
        default=[],
    )
    coordinates: Optional[List[DataVariable]] = Field(
        default=None,
        title="Coordinates",
        description="Coordinate variables that provide values along a dimension",
    )
    includedInDataCatalog: Optional[DataCatalog] = Field(
        default=None,
        title="DataCatalog",
        description="A data catalog which contains this dataset.",
    )
    additionalProperty: Optional[Union[str, List[str], PropertyValue, List[PropertyValue]]] = Field(
        title="Additional properties",
        default=None,
        description="Additional properties of the dataset that don't fit into schema org.",
    )
    sourceOrganization: Optional[Organization] = Field(
        default=None,
        title="Source organization",
        description="The organization that provided the data for this dataset.",
    )

    # ---------------------------------------------
    # make required CoreMetadata fields "Optional",
    # but preserve the metadata defined in the
    # parent class
    # ---------------------------------------------
    name: Optional[str] = Field(
        default=None,
        title="Name or title",
        description="A text string with a descriptive name or title for the dataset.",
    )
    description: Optional[str] = Field(
        default=None,
        title="Description or abstract",
        description="A text string containing a description/abstract for the dataset.",
    )
