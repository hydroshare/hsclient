from hs_rdf.schemas.enums import CoverageType, DateType, RelationType, UserIdentifierType
from hs_rdf.utils import to_coverage_dict


def split_dates(cls, values):
    if "created" in values:
        return values

    assert "dates" in values

    for date in values['dates']:
        if date['type'] == DateType.created:
            values["created"] = date['value']
        elif date['type'] == DateType.modified:
            values["modified"] = date['value']
        elif date['type'] == DateType.published:
            values["published"] = date['value']
    del values["dates"]
    return values


def split_coverages(cls, values):
    from hs_rdf.schemas.fields import BoxCoverage, PeriodCoverage, PointCoverage

    if "spatial_coverage" in values or "period_coverage" in values:
        return values

    assert "coverages" in values

    for coverage in values['coverages']:
        if coverage['type'] == CoverageType.period:
            values["period_coverage"] = PeriodCoverage(**to_coverage_dict(coverage['value']))
        elif coverage['type'] == CoverageType.box:
            values["spatial_coverage"] = BoxCoverage(**to_coverage_dict(coverage['value']))
        elif coverage['type'] == CoverageType.point:
            values["spatial_coverage"] = PointCoverage(**to_coverage_dict(coverage['value']))
    del values["coverages"]
    return values


def parse_additional_metadata(cls, values):
    if "extended_metadata" in values:
        value = values["extended_metadata"]
        if isinstance(value, list):
            parsed = {}
            for em in value:
                parsed[em['key']] = em['value']
            values["additional_metadata"] = parsed
            del values["extended_metadata"]
    return values


def parse_abstract(cls, values):
    if "description" in values:
        value = values["description"]
        if isinstance(value, dict) and "abstract" in value:
            values['abstract'] = value['abstract']
            del values['description']
    return values


def parse_url(cls, values):
    if "rdf_subject" in values:
        value = values["rdf_subject"]
        if value:
            values["url"] = values["rdf_subject"]
            del values["rdf_subject"]
    return values


def parse_relation(cls, values):
    if "type" in values or "value" in values:
        return values
    for relation_type in RelationType:
        if relation_type.name in values and values[relation_type.name]:
            values["type"] = relation_type
            values["value"] = values[relation_type.name]
            return values


def group_user_identifiers(cls, values):
    if "identifiers" not in values:
        identifiers = {}
        for identifier in UserIdentifierType:
            if identifier.name in values and values[identifier.name]:
                identifiers[identifier] = values[identifier.name]
        values["identifiers"] = identifiers
    return values
