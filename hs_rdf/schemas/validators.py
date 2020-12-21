from hs_rdf.schemas.data_structures import BoxSpatialReference, PointSpatialReference, \
    MultidimensionalBoxSpatialReference, MultidimensionalPointSpatialReference
from hs_rdf.schemas.enums import SpatialReferenceType, MultidimensionalSpatialReferenceType
from hs_rdf.utils import to_coverage_dict


def parse_spatial_reference(cls, value):
    if not value:
        return value
    if value['type'] == SpatialReferenceType.box:
        return BoxSpatialReference(**to_coverage_dict(value['value']))
    if value['type'] == SpatialReferenceType.point:
        return PointSpatialReference(**to_coverage_dict(value['value']))
    return value

def parse_multidimensional_spatial_reference(cls, value):
    if value['type'] == MultidimensionalSpatialReferenceType.box:
        d = to_coverage_dict(value['value'])
        return MultidimensionalBoxSpatialReference(**d)
    if value['type'] == MultidimensionalSpatialReferenceType.point:
        d = to_coverage_dict(value['value'])
        return MultidimensionalPointSpatialReference(**d)
    return value

def parse_identifier(cls, value):
    if isinstance(value, dict) and "hydroshare_identifier" in value:
        return value['hydroshare_identifier']
    return value

def parse_sources(cls, value):
    if len(value) > 0 and isinstance(value[0], dict):
        return [f['is_derived_from'] for f in value]
    return value

def parse_rdf_sources(cls, value):
    if len(value) > 0 and isinstance(value[0], str):
        return [{"is_derived_from": v} for v in value]
    return value

def rdf_parse_extended_metadata(cls, value):
    from hs_rdf.schemas.fields import ExtendedMetadataInRDF
    assert isinstance(value, list)
    if len(value) > 0:
        if isinstance(value[0], ExtendedMetadataInRDF):
            return value
    return [{"key": key, "value": val} for key, val in value.items()]

def rdf_parse_identifier(cls, value):
    if isinstance(value, str):
        return {"hydroshare_identifier": value}
    return value

def sort_creators(cls, creators):
    if not creators:
        raise ValueError("creators list must have at least one creator")
    if isinstance(next(iter(creators)), dict):
        for index, creator in enumerate(creators):
            creator["creator_order"] = index + 1
        return creators
    return sorted(creators, key=lambda creator: creator.creator_order)

def creators_not_empty(cls, creators):
    if len(creators) == 0:
        raise ValueError("Creator list must contain at least one creator")
    return creators

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

        # check the user exists for the provided user id
        #if not User.objects.filter(pk=user_id).exists():
        #    raise ValidationError(err_message)
