"""Helpers for translating between schema aggregation types and legacy hsmodels aggregation types."""

from __future__ import annotations

from typing import Optional, Union

from hsmodels.schemas.enums import AggregationType

from hsclient.schema.dataset import AdditionalType


class AggregationTypeAdapter:
    """Convert aggregation types between schema and legacy hsmodels representations."""

    _ADDITIONAL_TO_LEGACY = {
        AdditionalType.GEOGRAPHIC_FEATURE: AggregationType.GeographicFeatureAggregation,
        AdditionalType.GEOGRAPHIC_RASTER: AggregationType.GeographicRasterAggregation,
        AdditionalType.MULTIDIMENSIONAL: AggregationType.MultidimensionalAggregation,
        AdditionalType.TABULAR: AggregationType.CSVFileAggregation,
        AdditionalType.SINGLE_FILE: AggregationType.SingleFileAggregation,
        AdditionalType.FILE_SET: AggregationType.FileSetAggregation,
    }

    _LEGACY_TO_ADDITIONAL = {
        legacy_type: additional_type for additional_type, legacy_type in _ADDITIONAL_TO_LEGACY.items()
    }

    @classmethod
    def to_legacy_aggregation_type(cls, aggregation_type: Optional[AdditionalType]) -> Optional[AggregationType]:
        """Convert a schema AdditionalType into the matching legacy hsmodels AggregationType."""

        if aggregation_type is None:
            return None
        return cls._ADDITIONAL_TO_LEGACY.get(aggregation_type)

    @classmethod
    def to_aggregation_type(cls, aggregation_type: Optional[Union[AggregationType, str]]) -> Optional[AdditionalType]:
        """Convert a legacy hsmodels AggregationType into the matching schema AdditionalType."""

        if aggregation_type is None:
            return None
        if isinstance(aggregation_type, str):
            try:
                aggregation_type = AggregationType[aggregation_type]
            except KeyError:
                try:
                    aggregation_type = AggregationType(aggregation_type)
                except ValueError:
                    return None
        return cls._LEGACY_TO_ADDITIONAL.get(aggregation_type)
