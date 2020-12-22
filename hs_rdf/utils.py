from datetime import datetime

from hs_rdf.schemas.enums import AggregationType


def to_coverage_dict(value):
    value_dict = {}
    for key_value in value.split("; "):
        k, v = key_value.split("=")
        value_dict[k] = v
    return value_dict

def to_coverage_value_string(value: dict):
    return "; ".join(["=".join([key, val.isoformat() if isinstance(val, datetime) else str(val)])
                      for key, val in value.items()
                      if key != "type" and val])


def is_aggregation(path):
    return path.endswith('#aggregation')


def main_file_type(type: AggregationType):
    if type == AggregationType.GeographicRasterAggregation:
        return ".vrt"
    if type == AggregationType.MultidimensionalAggregation:
        return ".nc"
    if type == AggregationType.GeographicFeatureAggregation:
        return ".shp"
    if type == AggregationType.ReferencedTimeSeriesAggregation:
        return ".refts.json"
    if type == AggregationType.TimeSeriesAggregation:
        return ".sqlite"
    return None