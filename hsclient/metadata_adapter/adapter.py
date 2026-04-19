from typing import Union

from hsclient.metadata_adapter.legacy_resource_models import LegacyResourceMetadata
from hsclient.metadata_adapter.resource_models import SchemaOrgResourceMetadata
from hsclient.metadata_adapter.legacy_resource_adapter import LegacyResourceMetadataAdapter
from hsclient.metadata_adapter.resource_adapter import ResourceMetadataAdapter


class MetadataAdapter:
    @staticmethod
    def to_resource_metadata(legacy_metadata: Union[LegacyResourceMetadata, dict]) -> SchemaOrgResourceMetadata:
        if isinstance(legacy_metadata, LegacyResourceMetadata):
            adapter = LegacyResourceMetadataAdapter(**legacy_metadata.model_dump())
        else:
            adapter = LegacyResourceMetadataAdapter(**legacy_metadata)
        return adapter.to_resource_metadata()

    @staticmethod
    def to_legacy_resource_metadata(metadata: Union[SchemaOrgResourceMetadata, dict]) -> LegacyResourceMetadata:
        if isinstance(metadata, SchemaOrgResourceMetadata):
            adapter = ResourceMetadataAdapter(**metadata.model_dump())
        else:
            adapter = ResourceMetadataAdapter(**metadata)
        return adapter.to_legacy_resource_metadata()
