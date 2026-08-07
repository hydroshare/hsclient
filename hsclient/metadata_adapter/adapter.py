from typing import Union

from hsclient.metadata_adapter.legacy_resource_adapter import LegacyResourceMetadataAdapter
from hsclient.metadata_adapter.legacy_resource_models import LegacyResourceMetadata
from hsclient.metadata_adapter.netcdf_adapter import NetCDFMetadataAdapter
from hsclient.metadata_adapter.raster_adapter import RasterMetadataAdapter
from hsclient.metadata_adapter.resource_adapter import ResourceMetadataAdapter
from hsclient.metadata_adapter.resource_models import SchemaOrgResourceMetadata
from hsclient.schema.dataset import ScientificDataset
from hsclient.schema.legacy.netcdf import MultidimensionalMetadata
from hsclient.schema.legacy.raster import GeographicRasterMetadata


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

    @staticmethod
    def to_legacy_geographic_raster_metadata(metadata: Union[ScientificDataset, dict]) -> GeographicRasterMetadata:
        return RasterMetadataAdapter.to_legacy_geographic_raster_metadata(metadata)

    @staticmethod
    def to_geographic_raster_metadata(metadata: Union[GeographicRasterMetadata, dict]) -> ScientificDataset:
        return RasterMetadataAdapter.to_geographic_raster_metadata(metadata)

    @staticmethod
    def to_legacy_multidimensional_metadata(metadata: Union[ScientificDataset, dict]) -> MultidimensionalMetadata:
        return NetCDFMetadataAdapter.to_legacy_multidimensional_metadata(metadata)

    @staticmethod
    def to_multidimensional_metadata(metadata: Union[MultidimensionalMetadata, dict]) -> ScientificDataset:
        return NetCDFMetadataAdapter.to_multidimensional_metadata(metadata)
