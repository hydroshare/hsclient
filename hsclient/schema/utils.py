from typing import Any, Dict, Union

from ..metadata_adapter.legacy_resource_models import LegacyResourceMetadata
from ..metadata_adapter.adapter import MetadataAdapter
from .dataset import ScientificDataset

def load_json(json_data: Dict[str, Any], data_path: str) -> Union[LegacyResourceMetadata, ScientificDataset]:
    """Loads JSON metadata into the appropriate schema model based on file path."""

    if data_path.endswith("/.hsjsonld/dataset_metadata.json"):
        return MetadataAdapter.to_legacy_resource_metadata(json_data)

    # TODO: Need to convert an instance of ScientificDataset to corresponding
    # content type legacy metadata model
    return ScientificDataset.model_validate(json_data)
