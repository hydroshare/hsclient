from typing import Any, Dict, Union

from ..metadata_adapter.legacy_resource_models import LegacyResourceMetadata
from ..metadata_adapter.adapter import MetadataAdapter
from .base import Place, GeoShape
from .dataset import ScientificDataset
from pydantic import ValidationError

def load_json(json_data: Dict[str, Any], data_path: str) -> Union[LegacyResourceMetadata, ScientificDataset]:
    """Loads JSON metadata into the appropriate schema model based on file path."""
    # TODO: PK: hydroshare needs to be fixed so that relation has the valid data.
    # if 'relation' in json_data:
    #     json_data['relation'] = []

    if data_path.endswith("dataset_metadata.json"):
        return MetadataAdapter.to_legacy_resource_metadata(json_data)

    try:
        # Content type/aggregation metadata
        return ScientificDataset.model_validate(json_data)
    except ValidationError:
        spatial_coverage = json_data.get('spatialCoverage')
        spatial_coverage_model = None
        if spatial_coverage and  spatial_coverage['type'] == 'Place':
            geo = spatial_coverage['geo']
            if geo and geo['type'] == 'GeoShape':
                geo_model = GeoShape(box=geo['box'], validate_bbox=False)
                place = Place(name=spatial_coverage.get('name'), srs=spatial_coverage.get('srs'), geo=geo_model)
                spatial_coverage_model = place
                json_data['spatialCoverage'] = None
        content_type_metadata= ScientificDataset.model_validate(json_data)
        content_type_metadata.spatialCoverage = spatial_coverage_model
        # TODO: PK: Need to convert an instance of ScientificDataset to corresponding
        # content type legacy metadata model
        return content_type_metadata
