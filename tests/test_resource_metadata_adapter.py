import pytest
from hsmodels.schemas.enums import RelationType

from hsclient.metadata_adapter.adapter import MetadataAdapter
from hsclient.metadata_adapter.legacy_resource_adapter import LegacyResourceMetadataAdapter
from hsclient.metadata_adapter.legacy_resource_models import LegacyResourceMetadata
from hsclient.metadata_adapter.resource_adapter import ResourceMetadataAdapter
from hsclient.metadata_adapter.resource_models import SchemaOrgResourceMetadata
from hsclient.schema.base import LinkedData
from hsclient.schema.utils import load_json


def test_adapter_to_legacy_resource_metadata() -> None:
    metadata = {
        "@context": "https://hydroshare.org/schema",
        "@type": "CreativeWork",
        "additionalType": "CompositeResource",
        "name": "Schema Title",
        "description": "Schema Abstract",
        "url": "https://example.com/resource",
        "identifier": ["https://example.com/id", "doi:10.1/example"],
        "creator": [
            {
                "@type": "Person",
                "name": "Doe, Jane",
                "email": "jane@example.com",
                "identifier": "https://orcid.org/0000-0001-2345-6789",
                "affiliation": {"@type": "Organization", "name": "CUAHSI"},
            }
        ],
        "contributor": [{"@type": "Organization", "name": "Utah State University", "url": "https://usu.edu"}],
        "dateCreated": "2024-01-01T00:00:00",
        "dateModified": "2024-01-02T00:00:00",
        "datePublished": "2024-01-03T00:00:00",
        "keywords": ["hydrology", "water"],
        "inLanguage": "eng",
        "license": {"@type": "CreativeWork", "name": "CC-BY-4.0", "url": "https://example.com/license"},
        "provider": {"@type": "Organization", "name": "HydroShare", "url": "https://www.hydroshare.org/"},
        "publisher": {"@type": "Organization", "name": "CUAHSI HydroShare", "url": "https://www.hydroshare.org/"},
        "funding": [
            {
                "@type": "Grant",
                "name": "Grant Title",
                "identifier": "NSF-123",
                "funder": {"@type": "Organization", "name": "NSF", "url": "https://nsf.gov"},
            }
        ],
        "spatialCoverage": {
            "@type": "Place",
            "name": "Logan",
            # Resource-level box token order is "N E S W" (north, east, south, west)
            "geo": {"@type": "GeoShape", "box": "42.0 -111.0 41.5 -111.5"},
            "srs": {"@type": "SpatialReference", "name": "WGS 84 EPSG:4326", "srsType": "geographic"},
        },
        "temporalCoverage": {"startDate": "2024-01-01T00:00:00", "endDate": "2024-01-31T00:00:00"},
        "hasPart": [
            {"@type": "CreativeWork", "name": "Child resource", "url": "https://example.com/child"},
            {"@id": "https://example.com/linked-child"},
        ],
        "relation": [{"name": "References", "description": "Journal article", "url": "https://example.com/paper"}],
        # "relations": [{"type": "The content of this resource references", "value": "Journal article https://example.com/paper"}],
        "citation": ["Citation text"],
        "creativeWorkStatus": {"name": "Public"},
        "additionalProperty": [{"name": "custom-key", "value": "custom-value"}],
        "version": "2.0",
    }

    result = MetadataAdapter.to_legacy_resource_metadata(metadata)

    assert isinstance(result, LegacyResourceMetadata)
    assert result.type == "CompositeResource"
    assert result.title == "Schema Title"
    assert result.abstract == "Schema Abstract"
    assert str(result.identifier) == "https://example.com/id"
    assert result.additional_metadata == {"custom-key": "custom-value"}
    assert result.publisher.name == "CUAHSI HydroShare"
    assert str(result.publisher.url) == "https://www.hydroshare.org/"
    assert result.period_coverage.start.isoformat() == "2024-01-01T00:00:00"
    assert result.period_coverage.end.isoformat() == "2024-01-31T00:00:00"
    assert result.spatial_coverage.name == "Logan"
    assert result.spatial_coverage.northlimit == 42.0
    assert result.spatial_coverage.eastlimit == -111.0
    assert result.spatial_coverage.southlimit == 41.5
    assert result.spatial_coverage.westlimit == -111.5
    assert result.spatial_coverage.projection == "WGS 84 EPSG:4326"
    assert result.citation == "Citation text"
    assert len(result.relations) == 1
    assert result.relations[0].type == RelationType.references
    assert result.relations[0].value == "Journal article, https://example.com/paper"
    assert result.contributors[0].organization == "Utah State University"
    assert str(result.contributors[0].homepage) == "https://usu.edu/"
    assert result.created.isoformat() == "2024-01-01T00:00:00"
    assert result.modified.isoformat() == "2024-01-02T00:00:00"
    assert result.published.isoformat() == "2024-01-03T00:00:00"
    assert result.subjects == ["hydrology", "water"]
    assert result.sharing_status == "public"
    assert result.isPartOf == []
    assert len(result.hasPart) == 2
    # Check HasPart model format
    assert str(result.hasPart[0].url) == "https://example.com/child"
    assert result.hasPart[0].name == "Child resource"
    # Check LinkedData format
    assert isinstance(result.hasPart[1], LinkedData)
    assert str(result.hasPart[1].id) == "https://example.com/linked-child"
    assert result.rights.statement == "CC-BY-4.0"
    assert str(result.rights.url) == "https://example.com/license"
    assert result.awards[0].title == "Grant Title"
    assert result.awards[0].number == "NSF-123"
    assert result.awards[0].funding_agency_name == "NSF"
    assert str(result.awards[0].funding_agency_url) == "https://nsf.gov/"
    assert result.creators[0].name == "Doe, Jane"
    assert result.creators[0].email == "jane@example.com"
    assert result.creators[0].organization == "CUAHSI"
    assert result.creators[0].identifiers == {"ORCID": "https://orcid.org/0000-0001-2345-6789"}
    assert result.provider.name == "HydroShare"
    assert str(result.provider.url) == "https://www.hydroshare.org/"
    assert result.version == "2.0"


def test_adapter_to_legacy_resource_metadata_with_linked_data_associated_media() -> None:
    """Test that associatedMedia with JSON-LD @id references (LinkedData) is parsed and passed through correctly."""
    manifest_url = "http://localhost:9000/resource/ef91f0cc664c4d68aa2b58f21567d84b/.hsjsonld/file_manifest.json"
    metadata = {
        "@type": "CreativeWork",
        "name": "Test Resource",
        "creator": [{"@type": "Person", "name": "Doe, Jane"}],
        "associatedMedia": [{"@id": manifest_url}],
    }

    result = MetadataAdapter.to_legacy_resource_metadata(metadata)

    assert isinstance(result, LegacyResourceMetadata)
    assert result.associatedMedia is not None
    assert isinstance(result.associatedMedia, list)
    assert len(result.associatedMedia) == 1
    assert isinstance(result.associatedMedia[0], LinkedData)
    assert str(result.associatedMedia[0].id) == manifest_url


@pytest.mark.parametrize(
    "relation_name,expected_type",
    [
        # HydroShare's copy/new_version operations store auto-generated relations using the
        # RelationType enum's value/description text rather than its name.
        ("The content of this resource is derived from", RelationType.source),
        ("This resource updates and replaces a previous version", RelationType.isVersionOf),
        # matching by value should also be case-insensitive, same as the existing name match
        ("the content of this resource is derived from", RelationType.source),
    ],
)
def test_to_legacy_relations_matches_relation_type_by_value(relation_name, expected_type) -> None:
    """A relation whose name is the RelationType's value/description text (rather than its
    enum name) should still resolve to the correct legacy relation type."""
    adapter = ResourceMetadataAdapter(relation=[{"name": relation_name}])

    legacy_relations = adapter.to_legacy_relations()

    assert len(legacy_relations) == 1
    assert legacy_relations[0].type == expected_type


def test_to_legacy_relations_unknown_name_raises() -> None:
    adapter = ResourceMetadataAdapter(relation=[{"name": "not a real relation name"}])

    with pytest.raises(ValueError):
        adapter.to_legacy_relations()


def test_adapter_to_schema_org_metadata() -> None:
    metadata = {
        "type": "CompositeResource",
        "title": "Legacy Title",
        "abstract": "Legacy Abstract",
        "url": "https://example.com/resource",
        "identifier": "https://example.com/id",
        "creators": [
            {
                "name": "Doe, Jane",
                "email": "jane@example.com",
                "organization": "CUAHSI",
                "identifiers": {"ORCID": "https://orcid.org/0000-0001-2345-6789"},
            }
        ],
        "contributors": [{"organization": "Utah State University", "homepage": "https://usu.edu"}],
        "created": "2024-01-01T00:00:00",
        "modified": "2024-01-02T00:00:00",
        "published": "2024-01-03T00:00:00",
        "subjects": ["hydrology", "water"],
        "language": "eng",
        "rights": {"statement": "CC-BY-4.0", "url": "https://example.com/license"},
        "awards": [
            {
                "funding_agency_name": "NSF",
                "title": "Grant Title",
                "number": "NSF-123",
                "funding_agency_url": "https://nsf.gov",
            }
        ],
        "spatial_coverage": {
            "type": "box",
            "name": "Logan",
            "northlimit": 42.0,
            "eastlimit": -111.0,
            "southlimit": 41.5,
            "westlimit": -111.5,
            "units": "Decimal degrees",
            "projection": "WGS 84 EPSG:4326",
        },
        "period_coverage": {"start": "2024-01-01T00:00:00", "end": "2024-01-31T00:00:00"},
        "relations": [
            {
                "type": "The content of this resource references",
                "value": "Journal article, https://example.com/paper",
            },
        ],
        "citation": "Citation text",
        "additional_metadata": {"custom-key": "custom-value"},
        "publisher": {"name": "CUAHSI HydroShare", "url": "https://www.hydroshare.org/"},
        "version": "1.0",
    }

    result = MetadataAdapter.to_resource_metadata(metadata)

    assert isinstance(result, SchemaOrgResourceMetadata)
    assert result.type == "CreativeWork"
    assert result.additionalType == "CompositeResource"
    assert result.name == "Legacy Title"
    assert result.description == "Legacy Abstract"
    assert str(result.url) == "https://example.com/resource"
    assert result.identifier == ["https://example.com/id"]
    assert result.citation == ["Citation text"]
    assert result.creator[0].name == "Doe, Jane"
    assert result.contributor[0].name == "Utah State University"
    assert result.dateCreated.isoformat() == "2024-01-01T00:00:00"
    assert result.dateModified.isoformat() == "2024-01-02T00:00:00"
    assert result.datePublished.isoformat() == "2024-01-03T00:00:00"
    assert result.keywords == ["hydrology", "water"]
    assert result.additionalProperty[0].name == "custom-key"
    assert result.additionalProperty[0].value == "custom-value"
    assert result.publisher.name == "CUAHSI HydroShare"
    assert str(result.publisher.url) == "https://www.hydroshare.org/"
    assert len(result.relation) == 1
    assert result.relation[0].name == "references"
    assert result.inLanguage == "eng"
    assert result.license.name == "CC-BY-4.0"
    assert str(result.license.url) == "https://example.com/license"
    assert result.funding[0].name == "Grant Title"
    assert result.funding[0].identifier == "NSF-123"
    assert result.funding[0].funder.name == "NSF"
    assert str(result.funding[0].funder.url) == "https://nsf.gov/"
    assert result.spatialCoverage.geo.box == "42.0 -111.0 41.5 -111.5"
    assert result.spatialCoverage.srs.name == "WGS 84 EPSG:4326"
    assert result.spatialCoverage.srs.srsType == "geographic"
    assert result.temporalCoverage.startDate.isoformat() == "2024-01-01T00:00:00"
    assert result.temporalCoverage.endDate.isoformat() == "2024-01-31T00:00:00"
    assert result.provider.name == "HydroShare"
    assert str(result.provider.url) == "https://www.hydroshare.org/"
    assert result.version == "1.0"


def test_load_json_returns_legacy_resource_metadata_for_resource_metadata_json_file() -> None:
    metadata = {
        "@context": "https://hydroshare.org/schema",
        "@type": "CreativeWork",
        "additionalType": "CompositeResource",
        "name": "Schema Title",
        "description": "Schema Abstract",
        "url": "https://example.com/resource",
        "identifier": ["https://example.com/id"],
        "creator": [{"@type": "Person", "name": "Doe, Jane"}],
        "contributor": [{"@type": "Organization", "name": "Utah State University", "url": "https://usu.edu"}],
        "dateCreated": "2024-01-01T00:00:00",
        "dateModified": "2024-01-02T00:00:00",
        "datePublished": "2024-01-03T00:00:00",
        "publisher": {"@type": "Organization", "name": "HydroShare", "url": "https://www.hydroshare.org/"},
        "keywords": ["hydrology"],
        "inLanguage": "eng",
        "license": {"@type": "CreativeWork", "name": "CC-BY-4.0", "url": "https://example.com/license"},
        "funding": [
            {
                "@type": "Grant",
                "name": "Grant Title",
                "identifier": "NSF-123",
                "funder": {"@type": "Organization", "name": "NSF", "url": "https://nsf.gov"},
            }
        ],
        "spatialCoverage": {
            "@type": "Place",
            "name": "Logan",
            # Resource-level box token order is "N E S W" (north, east, south, west)
            "geo": {"@type": "GeoShape", "box": "42.0 -111.0 41.5 -111.5"},
        },
        "temporalCoverage": {"startDate": "2024-01-01T00:00:00", "endDate": "2024-01-31T00:00:00"},
        "relation": [{"name": "References", "description": "Journal article", "url": "https://example.com/paper"}],
        "hasPart": [
            {"@type": "CreativeWork", "name": "Child resource", "url": "https://example.com/child"},
            {"@id": "https://example.com/linked-child"},
        ],
        "creativeWorkStatus": {"name": "Public"},
        "provider": {"@type": "Organization", "name": "HydroShare", "url": "https://www.hydroshare.org/"},
        "citation": ["Citation text"],
        "additionalProperty": [{"name": "custom-key", "value": "custom-value"}],
        "version": "3.0",
    }

    result = load_json(metadata, "123/.hsjsonld/dataset_metadata.json")

    assert isinstance(result, LegacyResourceMetadata)
    assert result.title == "Schema Title"
    assert result.abstract == "Schema Abstract"
    assert str(result.url) == "https://example.com/resource"
    assert str(result.identifier) == "https://example.com/id"
    assert result.creators[0].name == "Doe, Jane"
    assert result.contributors[0].organization == "Utah State University"
    assert str(result.contributors[0].homepage) == "https://usu.edu/"
    assert result.created.isoformat() == "2024-01-01T00:00:00"
    assert result.modified.isoformat() == "2024-01-02T00:00:00"
    assert result.published.isoformat() == "2024-01-03T00:00:00"
    assert result.subjects == ["hydrology"]
    assert result.language == "eng"
    assert result.rights.statement == "CC-BY-4.0"
    assert str(result.rights.url) == "https://example.com/license"
    assert result.awards[0].funding_agency_name == "NSF"
    assert result.awards[0].title == "Grant Title"
    assert result.awards[0].number == "NSF-123"
    assert str(result.awards[0].funding_agency_url) == "https://nsf.gov/"
    assert result.spatial_coverage.name == "Logan"
    assert result.spatial_coverage.northlimit == 42.0
    assert result.spatial_coverage.eastlimit == -111.0
    assert result.spatial_coverage.southlimit == 41.5
    assert result.spatial_coverage.westlimit == -111.5
    assert result.period_coverage.start.isoformat() == "2024-01-01T00:00:00"
    assert result.period_coverage.end.isoformat() == "2024-01-31T00:00:00"
    assert result.sharing_status == "public"
    assert result.additional_metadata == {"custom-key": "custom-value"}
    assert result.publisher.name == "HydroShare"
    assert str(result.publisher.url) == "https://www.hydroshare.org/"
    assert len(result.relations) == 1
    assert result.relations[0].type == RelationType.references
    assert result.relations[0].value == "Journal article, https://example.com/paper"
    assert result.isPartOf == []
    assert len(result.hasPart) == 2
    # Check HasPart model format
    assert str(result.hasPart[0].url) == "https://example.com/child"
    assert result.hasPart[0].name == "Child resource"
    # Check LinkedData format
    assert isinstance(result.hasPart[1], LinkedData)
    assert str(result.hasPart[1].id) == "https://example.com/linked-child"
    assert result.provider.name == "HydroShare"
    assert str(result.provider.url) == "https://www.hydroshare.org/"
    assert result.citation == "Citation text"
    assert result.version == "3.0"


@pytest.mark.parametrize(
    "sharing_status,creative_work_status_name",
    [
        ("public", "Public"),
        ("private", "Private"),
        ("published", "Published"),
        ("discoverable", "Discoverable"),
        ("draft", "Draft"),
        ("incomplete", "Incomplete"),
        ("obsolete", "Obsolete"),
    ],
)
def test_legacy_to_dataset_creative_work_status(sharing_status, creative_work_status_name) -> None:
    """Every legacy sharing_status value should convert to its matching schema.org
    creativeWorkStatus DefinedTerm."""
    adapter = LegacyResourceMetadataAdapter(creators=[{"name": "Doe, Jane"}], sharing_status=sharing_status)

    creative_work_status = adapter.to_dataset_creative_work_status()

    assert creative_work_status.name == creative_work_status_name


@pytest.mark.parametrize(
    "creative_work_status_name,sharing_status",
    [
        ("Public", "public"),
        ("Private", "private"),
        ("Published", "published"),
        ("Discoverable", "discoverable"),
        ("Draft", "draft"),
        ("Incomplete", "incomplete"),
        ("Obsolete", "obsolete"),
    ],
)
def test_dataset_to_legacy_sharing_status(creative_work_status_name, sharing_status) -> None:
    """Every schema.org creativeWorkStatus DefinedTerm should convert to its matching legacy
    sharing_status value."""
    adapter = ResourceMetadataAdapter(creativeWorkStatus={"name": creative_work_status_name})

    assert adapter.to_legacy_sharing_status() == sharing_status


def test_dataset_to_legacy_sharing_status_none() -> None:
    adapter = ResourceMetadataAdapter(creativeWorkStatus=None)

    assert adapter.to_legacy_sharing_status() is None


def test_dataset_to_legacy_sharing_status_unknown_raises() -> None:
    adapter = ResourceMetadataAdapter.model_construct(creativeWorkStatus="unrecognized")

    with pytest.raises(ValueError):
        adapter.to_legacy_sharing_status()


def test_unknown_schema_org_field_survives_object_input_round_trip() -> None:
    """A schema.org field with no matching legacy field must not be silently dropped: it should
    be captured into LegacyResourceMetadata.extra_columns, then replayed back unchanged when
    converting back to schema.org form."""
    metadata = {
        "name": "Test Resource",
        "creator": [{"name": "Doe, Jane"}],
        "someFutureField": "abc123",
    }

    legacy = MetadataAdapter.to_legacy_resource_metadata(metadata)

    assert legacy.extra_columns == {"someFutureField": "abc123"}

    dataset = MetadataAdapter.to_resource_metadata(legacy)

    assert dataset.model_extra == {"someFutureField": "abc123"}
    assert dataset.model_dump(exclude_none=True)["someFutureField"] == "abc123"


def test_unknown_legacy_field_survives_dict_input_round_trip() -> None:
    """MetadataAdapter.to_resource_metadata() also accepts a raw legacy-shaped dict directly
    (not just a LegacyResourceMetadata instance) -- an unrecognized key on that path must
    survive via LegacyResourceMetadataAdapter's own extra_columns capture."""
    legacy_dict = {
        "title": "Test Resource",
        "creators": [{"name": "Doe, Jane"}],
        "someLegacySideUnknownField": "xyz",
    }

    dataset = MetadataAdapter.to_resource_metadata(legacy_dict)

    assert dataset.model_extra == {"someLegacySideUnknownField": "xyz"}


def test_subject_of_round_trips_as_named_field() -> None:
    """subjectOf is a known schema.org field -- it should round-trip
    as a real, frozen field rather than falling into the generic extra_columns catch-all."""
    metadata = {
        "name": "Test Resource",
        "creator": [{"name": "Doe, Jane"}],
        "subjectOf": [{"name": "A related paper", "url": "https://doi.org/10.1/xyz"}],
    }

    legacy = MetadataAdapter.to_legacy_resource_metadata(metadata)

    assert legacy.subjectOf[0].name == "A related paper"
    assert str(legacy.subjectOf[0].url) == "https://doi.org/10.1/xyz"
    with pytest.raises(AttributeError):
        legacy.subjectOf = []

    dataset = MetadataAdapter.to_resource_metadata(legacy)

    assert dataset.subjectOf[0].name == "A related paper"
