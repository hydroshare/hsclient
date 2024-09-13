from collections import namedtuple
from os.path import splitext
from urllib.request import pathname2url

from hsmodels.schemas.enums import AggregationType

CSVColumnDataType = namedtuple('CSVColumnDataType', ['string', 'number', 'datetime', 'boolean'])(
    'string', 'number', 'datetime', 'boolean'
)


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
    if type == AggregationType.CSVFileAggregation:
        return ".csv"
    return None


def attribute_filter(o, key, value) -> bool:
    if isinstance(o, list):
        if key == "contains":
            return value in o
    if isinstance(o, dict):
        if key == "key":
            return value in o
        if key == "value":
            return value in o.values()
    if "__" in key:
        keys = key.split("__", 1)
        if not hasattr(o, keys[0]):
            return None
            # raise AttributeError(f"{o} has no attribute {keys[0]}")
        o = getattr(o, keys[0])
        return attribute_filter(o, keys[1], value)
    if not hasattr(o, key):
        return None
        # raise AttributeError(f"{o} has no attribute {key}")
    attr = getattr(o, key)
    return attr == value


def encode_resource_url(url):
    """
    URL encodes a full resource file/folder url.
    :param url: a string url
    :return: url encoded string
    """
    import urllib

    parsed_url = urllib.parse.urlparse(url)
    url_encoded_path = pathname2url(parsed_url.path)
    encoded_url = parsed_url._replace(path=url_encoded_path).geturl()
    return encoded_url


def is_folder(path):
    """Checks for an extension to determine if the path is to a folder"""
    return splitext(path)[1] == ''
