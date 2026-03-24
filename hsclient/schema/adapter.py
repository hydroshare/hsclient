from typing import Any, Dict, Mapping, Optional, Union

from hsmodels.schemas.resource import ResourceMetadata

from .base import PropertyValue
from .core import CoreMetadata

CoreMetadataInput = Union[CoreMetadata, Mapping[str, Any]]
ResourceMetadataInput = Union[ResourceMetadata, Mapping[str, Any]]

_DEFAULT_PROVIDER = {
    "@type": "Organization",
    "name": "HydroShare",
    "url": "https://www.hydroshare.org/",
}

_LEGACY_RELATION_TYPE_MAP = {
    "This resource is part of": "The content of this resource is part of",
    "This resource includes": "This resource includes",
    "References": "The content of this resource references",
    "The content of this resource references": "The content of this resource references",
}


def _coerce_core_metadata(metadata: CoreMetadataInput) -> CoreMetadata:
    if isinstance(metadata, CoreMetadata):
        return metadata
    return CoreMetadata.model_validate(metadata)


def _coerce_resource_metadata(metadata: ResourceMetadataInput) -> ResourceMetadata:
    if isinstance(metadata, ResourceMetadata):
        return metadata
    return ResourceMetadata.model_validate(metadata)


def _drop_nones(data: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def _list_or_none(values: list[Any]) -> Optional[list[Any]]:
    return values or None


def _stringify_url(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _normalize_language(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "value"):
        return str(value.value)
    if hasattr(value, "name"):
        return str(value.name)
    return str(value)


def _normalize_keywords(values: Optional[list[str]]) -> Optional[list[str]]:
    if not values:
        return None
    if values == ["HydroShare"]:
        return None
    return values


def _normalize_orcid(orcid: Optional[str]) -> Optional[str]:
    if not orcid:
        return None
    if str(orcid).startswith("http"):
        return str(orcid)
    return f"https://orcid.org/{orcid}"


def _build_relation_value(description: Optional[str], url: Optional[str]) -> str:
    description = (description or "").strip()
    url = (url or "").strip()
    if description and url:
        return f"{description}, {url}"
    return description or url


def _split_relation_value(value: Optional[str]) -> tuple[str, str]:
    if not value:
        return "", ""
    if "," in value:
        description, url = value.rsplit(",", 1)
        return description.strip(), url.strip()
    return value.strip(), ""


def _additional_metadata_from_core(core_metadata: CoreMetadata) -> Optional[Dict[str, str]]:
    additional_property = core_metadata.additionalProperty
    if not additional_property:
        return None

    properties = additional_property if isinstance(additional_property, list) else [additional_property]
    additional_metadata: Dict[str, str] = {}
    for item in properties:
        if isinstance(item, str):
            continue

        name = getattr(item, "name", None)
        value = getattr(item, "value", None)
        if name is None or value is None:
            continue
        additional_metadata[str(name)] = str(value)

    return additional_metadata or None


def _additional_property_from_resource(resource_metadata: ResourceMetadata) -> Optional[list[PropertyValue]]:
    if not resource_metadata.additional_metadata:
        return None

    return [PropertyValue(name=name, value=value) for name, value in resource_metadata.additional_metadata.items()]


def _dump_model(value: Any) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    return value.model_dump(mode="json", exclude_none=True)


def _legacy_person_from_core(person: Any) -> Dict[str, Any]:
    person_type = getattr(person, "type", None)
    if person_type == "Organization":
        return _drop_nones(
            {
                "organization": getattr(person, "name", None),
                "homepage": _stringify_url(getattr(person, "url", None)),
                "address": getattr(person, "address", None),
            }
        )

    affiliation = getattr(person, "affiliation", None)
    orcid = _normalize_orcid(_stringify_url(getattr(person, "identifier", None)))
    identifiers = {"ORCID": orcid} if orcid else None
    return _drop_nones(
        {
            "name": getattr(person, "name", None),
            "email": getattr(person, "email", None),
            "organization": getattr(affiliation, "name", None),
            "identifiers": identifiers,
        }
    )


def _core_person_from_legacy(person: Any) -> Dict[str, Any]:
    if getattr(person, "name", None):
        identifiers = getattr(person, "identifiers", None) or {}
        identifier = identifiers.get("ORCID")
        affiliation_name = getattr(person, "organization", None)
        return _drop_nones(
            {
                "@type": "Person",
                "name": person.name,
                "email": getattr(person, "email", None),
                "identifier": _stringify_url(identifier),
                "affiliation": {"@type": "Organization", "name": affiliation_name} if affiliation_name else None,
            }
        )

    return _drop_nones(
        {
            "@type": "Organization",
            "name": getattr(person, "organization", None),
            "url": _stringify_url(getattr(person, "homepage", None)),
            "address": getattr(person, "address", None),
        }
    )


def _legacy_rights_from_core(license_value: Any) -> Optional[Dict[str, str]]:
    if license_value is None:
        return None

    url = _stringify_url(getattr(license_value, "url", license_value))
    statement = getattr(license_value, "name", None) or url
    return _drop_nones({"statement": statement, "url": url})


def _core_license_from_legacy(rights: Any) -> Optional[Dict[str, str]]:
    if rights is None:
        return None
    return _drop_nones(
        {
            "@type": "CreativeWork",
            "name": getattr(rights, "statement", None),
            "url": _stringify_url(getattr(rights, "url", None)),
        }
    )


def _legacy_award_from_core(grant: Any) -> Dict[str, Any]:
    funder = getattr(grant, "funder", None)
    funding_agency_name = getattr(funder, "name", None) or getattr(grant, "name", None)
    title = getattr(grant, "name", None)
    if title == funding_agency_name:
        title = None

    return _drop_nones(
        {
            "funding_agency_name": funding_agency_name,
            "title": title,
            "number": getattr(grant, "identifier", None),
            "funding_agency_url": _stringify_url(getattr(funder, "url", None)),
        }
    )


def _core_award_from_legacy(award: Any) -> Dict[str, Any]:
    funding_agency_name = getattr(award, "funding_agency_name", None)
    return _drop_nones(
        {
            "@type": "Grant",
            "name": getattr(award, "title", None) or funding_agency_name,
            "identifier": getattr(award, "number", None),
            "funder": (
                {
                    "@type": "Organization",
                    "name": funding_agency_name,
                    "url": _stringify_url(getattr(award, "funding_agency_url", None)),
                }
                if funding_agency_name
                else None
            ),
        }
    )


def _legacy_spatial_from_core(spatial_coverage: Any) -> Optional[Dict[str, Any]]:
    if spatial_coverage is None:
        return None

    geo = getattr(spatial_coverage, "geo", None)
    geo_type = getattr(geo, "type", None)
    if geo_type == "GeoCoordinates":
        return _drop_nones(
            {
                "type": "point",
                "name": getattr(spatial_coverage, "name", None),
                "north": getattr(geo, "latitude", None),
                "east": getattr(geo, "longitude", None),
                "units": "Decimal degrees",
                "projection": "WGS 84 EPSG:4326",
            }
        )

    if geo_type == "GeoShape":
        try:
            parts = str(getattr(geo, "box", "")).split()
            if len(parts) != 4:
                return None
            north, east, south, west = [float(value) for value in parts]
        except (ValueError, AttributeError):
            return None

        return _drop_nones(
            {
                "type": "box",
                "name": getattr(spatial_coverage, "name", None),
                "northlimit": north,
                "eastlimit": east,
                "southlimit": south,
                "westlimit": west,
                "units": "Decimal degrees",
                "projection": "WGS 84 EPSG:4326",
            }
        )

    return None


def _core_spatial_from_legacy(spatial_coverage: Any) -> Optional[Dict[str, Any]]:
    if spatial_coverage is None:
        return None

    if getattr(spatial_coverage, "type", None) == "point":
        return _drop_nones(
            {
                "@type": "Place",
                "name": getattr(spatial_coverage, "name", None),
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": getattr(spatial_coverage, "north", None),
                    "longitude": getattr(spatial_coverage, "east", None),
                },
            }
        )

    return _drop_nones(
        {
            "@type": "Place",
            "name": getattr(spatial_coverage, "name", None),
            "geo": {
                "@type": "GeoShape",
                "box": (
                    f"{getattr(spatial_coverage, 'northlimit', None)} "
                    f"{getattr(spatial_coverage, 'eastlimit', None)} "
                    f"{getattr(spatial_coverage, 'southlimit', None)} "
                    f"{getattr(spatial_coverage, 'westlimit', None)}"
                ),
            },
        }
    )


def _legacy_period_from_core(period_coverage: Any) -> Optional[Dict[str, Any]]:
    if period_coverage is None:
        return None
    return _drop_nones(
        {
            "start": getattr(period_coverage, "startDate", None),
            "end": getattr(period_coverage, "endDate", None),
        }
    )


def _core_period_from_legacy(period_coverage: Any) -> Optional[Dict[str, Any]]:
    if period_coverage is None:
        return None
    return _drop_nones(
        {
            "startDate": getattr(period_coverage, "start", None),
            "endDate": getattr(period_coverage, "end", None),
        }
    )


def _legacy_relation_from_core(relation: Any, relation_type: str = "Other") -> Optional[Dict[str, str]]:
    if relation is None:
        return None

    if relation_type == "IsPartOf":
        relation_name = "The content of this resource is part of"
    elif relation_type == "HasPart":
        relation_name = "This resource includes"
    else:
        relation_name = _LEGACY_RELATION_TYPE_MAP.get(getattr(relation, "name", None), getattr(relation, "name", None))

    if relation_name is None:
        return None

    return {
        "type": relation_name,
        "value": _build_relation_value(
            getattr(relation, "description", None),
            _stringify_url(getattr(relation, "url", None)),
        ),
    }


def _core_relations_from_legacy(relations: list[Any]) -> Dict[str, list[Dict[str, Any]]]:
    relation_payload = {"isPartOf": [], "hasPart": [], "relation": []}
    for relation in relations:
        description, url = _split_relation_value(getattr(relation, "value", None))
        payload = _drop_nones(
            {
                "name": getattr(relation, "type", None),
                "description": description or None,
                "url": url or None,
            }
        )
        relation_type = getattr(relation, "type", None)
        if relation_type == "The content of this resource is part of":
            relation_payload["isPartOf"].append(payload)
        elif relation_type == "This resource includes":
            relation_payload["hasPart"].append(payload)
        else:
            relation_payload["relation"].append(payload)
    return relation_payload


def _legacy_relations_from_core(core_model: CoreMetadata) -> Optional[list[Dict[str, str]]]:
    relations = [
        *filter(None, (_legacy_relation_from_core(item, "IsPartOf") for item in (core_model.isPartOf or []))),
        *filter(None, (_legacy_relation_from_core(item, "HasPart") for item in (core_model.hasPart or []))),
        *filter(None, (_legacy_relation_from_core(item) for item in (core_model.relation or []))),
    ]
    return _list_or_none(relations)


def from_core_metadata(core_metadata: CoreMetadataInput) -> ResourceMetadata:
    core_model = _coerce_core_metadata(core_metadata)

    legacy_payload = _drop_nones(
        {
            "type": core_model.additionalType,
            "title": core_model.name,
            "abstract": core_model.description,
            "url": _stringify_url(core_model.url),
            "identifier": core_model.identifier[0] if core_model.identifier else None,
            "creators": [_legacy_person_from_core(person) for person in core_model.creator],
            "contributors": [_legacy_person_from_core(person) for person in (core_model.contributor or [])],
            "created": core_model.dateCreated,
            "modified": core_model.dateModified,
            "published": core_model.datePublished,
            "subjects": _normalize_keywords(core_model.keywords),
            "language": _normalize_language(core_model.inLanguage),
            "rights": _legacy_rights_from_core(core_model.license),
            "awards": [_legacy_award_from_core(grant) for grant in (core_model.funding or [])],
            "spatial_coverage": _legacy_spatial_from_core(core_model.spatialCoverage),
            "period_coverage": _legacy_period_from_core(core_model.temporalCoverage),
            "relations": _legacy_relations_from_core(core_model),
            "citation": core_model.citation[0] if core_model.citation else None,
            "additional_metadata": _additional_metadata_from_core(core_model),
            "publisher": _dump_model(core_model.publisher),
        }
    )

    return ResourceMetadata.model_validate(legacy_payload)


def to_core_metadata(resource_metadata: ResourceMetadataInput) -> CoreMetadata:
    resource_model = _coerce_resource_metadata(resource_metadata)
    relation_payload = _core_relations_from_legacy(resource_model.relations or [])

    core_payload = _drop_nones(
        {
            "@type": "CreativeWork",
            "additionalType": resource_model.type,
            "name": resource_model.title,
            "description": resource_model.abstract,
            "url": _stringify_url(resource_model.url),
            "identifier": [str(resource_model.identifier)] if resource_model.identifier else None,
            "creator": [_core_person_from_legacy(person) for person in (resource_model.creators or [])],
            "dateCreated": resource_model.created,
            "keywords": resource_model.subjects or ["HydroShare"],
            "license": _core_license_from_legacy(resource_model.rights),
            "provider": _DEFAULT_PROVIDER,
            "contributor": _list_or_none(
                [_core_person_from_legacy(person) for person in (resource_model.contributors or [])]
            ),
            "publisher": _dump_model(resource_model.publisher),
            "datePublished": resource_model.published,
            "inLanguage": resource_model.language,
            "dateModified": resource_model.modified,
            "funding": _list_or_none([_core_award_from_legacy(award) for award in (resource_model.awards or [])]),
            "temporalCoverage": _core_period_from_legacy(resource_model.period_coverage),
            "spatialCoverage": _core_spatial_from_legacy(resource_model.spatial_coverage),
            "isPartOf": _list_or_none(relation_payload["isPartOf"]),
            "hasPart": _list_or_none(relation_payload["hasPart"]),
            "relation": _list_or_none(relation_payload["relation"]),
            "additionalProperty": _list_or_none(
                [
                    property_value.model_dump(mode="json", by_alias=True, exclude_none=True)
                    for property_value in (_additional_property_from_resource(resource_model) or [])
                ]
            ),
            "citation": [resource_model.citation] if resource_model.citation else None,
        }
    )

    return CoreMetadata.model_validate(core_payload)


__all__ = ["from_core_metadata", "to_core_metadata"]
