from hs_rdf.schemas.enums import CoverageType, DateType
from hs_rdf.schemas.languages_iso import languages


def parse_rdf_sources(cls, value):
    if len(value) > 0 and isinstance(value[0], str):
        return [{"is_derived_from": v} for v in value]
    return value


def rdf_parse_extended_metadata(cls, value):
    from hs_rdf.schemas.rdf.fields import ExtendedMetadataInRDF

    assert isinstance(value, list)
    if len(value) > 0:
        if isinstance(value[0], ExtendedMetadataInRDF):
            return value
    return [{"key": key, "value": val} for key, val in value.items()]


def rdf_parse_identifier(cls, value):
    if isinstance(value, str):
        return {"hydroshare_identifier": value}
    return value


def language_constraint(cls, language):
    if language not in [code for code, verbose in languages]:
        raise ValueError("language '{}' must be a 3 letter iso language code".format(language))
    return language


def dates_constraint(cls, dates):
    assert len(dates) >= 2
    created = list(filter(lambda d: d.type == DateType.created, dates))
    assert len(created) == 1
    created = created[0]
    modified = list(filter(lambda d: d.type == DateType.modified, dates))
    assert len(modified) == 1
    modified = modified[0]

    assert modified.value >= created.value
    return dates


def coverages_constraint(cls, coverages):
    def one_or_none_of_type(type):
        cov = list(filter(lambda d: d.type == type, coverages))
        assert len(cov) <= 1

    one_or_none_of_type(CoverageType.point)
    one_or_none_of_type(CoverageType.period)
    one_or_none_of_type(CoverageType.box)
    return coverages


def coverages_spatial_constraint(cls, coverages):
    contains_point = any(c for c in coverages if c.type == CoverageType.point)
    contains_box = any(c for c in coverages if c.type == CoverageType.box)
    if contains_point:
        assert not contains_box, "Only one type of spatial coverage is allowed, point or box"
    return coverages


def sort_creators(cls, creators):
    if not creators:
        raise ValueError("creators list must have at least one creator")
    if isinstance(next(iter(creators)), dict):
        for index, creator in enumerate(creators):
            creator["creator_order"] = index + 1
        return creators
    return sorted(creators, key=lambda creator: creator.creator_order)
