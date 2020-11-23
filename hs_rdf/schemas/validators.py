from hs_rdf.schemas.enums import SpatialReferenceType, CoverageType
from hs_rdf.schemas.fields import BoxSpatialReference, PointSpatialReference, BoxCoverage, PointCoverage, \
    PeriodCoverage
from hs_rdf.utils import to_coverage_dict


def parse_spatial_reference(cls, value):
    if value['type'] == SpatialReferenceType.box:
        return BoxSpatialReference(**to_coverage_dict(value['value']))
    if value['type'] == SpatialReferenceType.point:
        return PointSpatialReference(**to_coverage_dict(value['value']))
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
