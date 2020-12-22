from hs_rdf.schemas import fields, enums
from hs_rdf.utils import to_coverage_dict


def parse_spatial_reference(cls, value):
    if not value:
        return value
    if value['type'] == enums.SpatialReferenceType.box:
        return fields.BoxSpatialReference(**to_coverage_dict(value['value']))
    if value['type'] == enums.SpatialReferenceType.point:
        return fields.PointSpatialReference(**to_coverage_dict(value['value']))
    return value

def parse_multidimensional_spatial_reference(cls, value):
    if value['type'] == enums.MultidimensionalSpatialReferenceType.box:
        d = to_coverage_dict(value['value'])
        return fields.MultidimensionalBoxSpatialReference(**d)
    if value['type'] == enums.MultidimensionalSpatialReferenceType.point:
        d = to_coverage_dict(value['value'])
        return fields.MultidimensionalPointSpatialReference(**d)
    return value

def parse_identifier(cls, value):
    if isinstance(value, dict) and "hydroshare_identifier" in value:
        return value['hydroshare_identifier']
    return value

def parse_sources(cls, value):
    if len(value) > 0 and isinstance(value[0], dict):
        return [f['is_derived_from'] for f in value]
    return value

def list_not_empty(cls, l):
    if len(l) == 0:
        raise ValueError("list must contain at least one entry")
    return l

def validate_user_url(value):
    """Validate that a URL is a valid URL for a hydroshare user."""
    err_message = '%s is not a valid url for hydroshare user' % value
    if value:
        url_parts = value.split('/')
        if len(url_parts) != 4:
            raise ValueError(err_message)
        if url_parts[1] != 'user':
            raise ValueError(err_message)

        try:
            user_id = int(url_parts[2])
        except ValueError:
            raise ValueError(err_message)
    return value
