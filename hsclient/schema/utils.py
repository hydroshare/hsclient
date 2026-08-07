from typing import Any, Dict, Union

from ..metadata_adapter.adapter import MetadataAdapter
from ..metadata_adapter.legacy_resource_models import LegacyResourceMetadata
from .dataset import AdditionalType, ScientificDataset
from .legacy.netcdf import MultidimensionalMetadata
from .legacy.raster import GeographicRasterMetadata


def load_json(
    json_data: Dict[str, Any], data_path: str
) -> Union[LegacyResourceMetadata, GeographicRasterMetadata, MultidimensionalMetadata, ScientificDataset]:
    """Load JSON metadata into the appropriate schema model based on file path and content type."""

    if data_path.endswith("/.hsjsonld/dataset_metadata.json"):
        return MetadataAdapter.to_legacy_resource_metadata(json_data)

    dataset = ScientificDataset.model_validate(json_data)

    if dataset.additionalType == AdditionalType.GEOGRAPHIC_RASTER:
        return MetadataAdapter.to_legacy_geographic_raster_metadata(json_data)

    if dataset.additionalType == AdditionalType.MULTIDIMENSIONAL:
        return MetadataAdapter.to_legacy_multidimensional_metadata(json_data)

    # TODO: MetadataAdapter needs to be implemented to handle other types of aggregations/content types.
    return dataset
