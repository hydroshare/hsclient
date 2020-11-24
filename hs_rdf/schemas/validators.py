from hs_rdf.schemas.enums import SpatialReferenceType, CoverageType, DateType, MultidimensionalSpatialReferenceType
from hs_rdf.schemas.fields import BoxSpatialReference, PointSpatialReference, BoxCoverage, PointCoverage, \
    PeriodCoverage, ExtendedMetadataInRDF, MultidimensionalBoxSpatialReference, MultidimensionalPointSpatialReference
from hs_rdf.utils import to_coverage_dict


def parse_spatial_reference(cls, value):
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

def parse_additional_metadata(cls, value):
    if isinstance(value, list):
        parsed = {}
        for em in value:
            parsed[em['key']] = em['value']
        return parsed
    return value

def parse_spatial_coverage(cls, value):
    if isinstance(value, list):
        for coverage in value:
            if coverage['type'] == CoverageType.box:
                return BoxCoverage(**to_coverage_dict(coverage['value']))
            if coverage['type'] == CoverageType.point:
                return PointCoverage(**to_coverage_dict(coverage['value']))
        return None
    return value

def parse_period_coverage(cls, value):
    if isinstance(value, list):
        for coverage in value:
            if coverage['type'] == CoverageType.period:
                return PeriodCoverage(**to_coverage_dict(coverage['value']))
        return None
    return value

def parse_period_coverage(cls, value):
    if isinstance(value, list):
        for coverage in value:
            if coverage['type'] == CoverageType.period:
                return PeriodCoverage(**to_coverage_dict(coverage['value']))
        return None
    return value

def parse_identifier(cls, value):
    if isinstance(value, dict) and "hydroshare_identifier" in value:
        return value['hydroshare_identifier']
    return value

def parse_abstract(cls, value):
    if isinstance(value, dict) and "abstract" in value:
        return value['abstract']
    return value

def parse_created(cls, value):
    if isinstance(value, list):
        for date in value:
            if date['type'] == DateType.created:
                return date['value']
        return None
    return value

def parse_published(cls, value):
    if isinstance(value, list):
        for date in value:
            if date['type'] == DateType.published:
                return date['value']
        return None
    return value

def parse_modified(cls, value):
    if isinstance(value, list):
        for date in value:
            if date['type'] == DateType.modified:
                return date['value']
        return None
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
    assert isinstance(value, list)
    if len(value) > 0:
        if isinstance(value[0], ExtendedMetadataInRDF):
            return value
    return [{"key": key, "value": val} for key, val in value.items()]

def rdf_parse_identifier(cls, value):
    if isinstance(value, str):
        return {"hydroshare_identifier": value}
    return value
