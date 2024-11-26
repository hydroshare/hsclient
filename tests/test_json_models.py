import json
import os

import pytest
from dateutil import parser
from hsmodels.schemas.enums import UserIdentifierType
from hsmodels.schemas.fields import Contributor, Creator

from hsclient.json_models import ResourcePreview, User


@pytest.fixture(scope="function")
def change_test_dir(request):
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture
def user(change_test_dir):
    with open("data/user.json", "r") as f:
        return User(**json.loads(f.read()))


def test_null_subject_areas():
    fields = {"subject_areas": None}
    o = User(**fields)
    assert o.subject_areas == []


def generate_resource_preview_test_data(authors_field):
    data = ResourcePreviewTestRequiredData.copy()
    data.update(authors_field)
    data = json.dumps(data)
    return data


ResourcePreviewTestRequiredData = {
    "resource_type": "CompositeResource",
    "resource_title": "Test Resource",
    "resource_id": "97523bdb7b174901b3fc2d89813458f1",
    "creator": "John Doe",
    "date_created": "2021-01-01T00:00:00.000Z",
    "date_last_updated": "2021-01-01T00:00:00.000Z",
    "public": True,
    "discoverable": True,
    "shareable": True,
    "immutable": False,
    "published": False,
    "resource_url": "http://beta.hydroshare.org/resource/97523bdb7b174901b3fc2d89813458f1/",
    "resource_map_url": "http://beta.hydroshare.org/resource/97523bdb7b174901b3fc2d89813458f1/map/",
    "science_metadata_url": "http://beta.hydroshare.org/resource/97523bdb7b174901b3fc2d89813458f1/science-metadata/",
}

authors = [{"authors": x} for x in [None, [], [None], [""], [[]]]]
AuthorsFieldResourcePreviewTestData = map(generate_resource_preview_test_data, authors)


@pytest.mark.parametrize("test_data", AuthorsFieldResourcePreviewTestData)
def test_resource_preview_authors_field_handles_none_cases(test_data):
    """verify all `authors` fields are instantiated with [] values.

    coerced `authors` field should be [] with following input:
        None
        []
        [None]
        [None, ""]
    """

    from_json = ResourcePreview.model_validate_json(test_data)

    assert from_json.authors == []


def test_resource_preview_authors_raises_validation_error_on_string_input():
    """verify that a string passed to authors field raises pydantic.ValidationError"""
    from pydantic import ValidationError

    data = ResourcePreviewTestRequiredData.copy()
    data.update({"authors": "should_fail"})
    data = json.dumps(data)

    with pytest.raises(ValidationError):
        ResourcePreview.model_validate_json(data)


def test_resource_preview_required_fields():
    resource_preview = ResourcePreview.model_validate_json(json.dumps(ResourcePreviewTestRequiredData))
    assert resource_preview.resource_type == "CompositeResource"
    assert resource_preview.resource_title == "Test Resource"
    assert resource_preview.resource_id == "97523bdb7b174901b3fc2d89813458f1"
    assert resource_preview.creator == "John Doe"
    assert resource_preview.date_created == "2021-01-01T00:00:00.000Z"
    assert resource_preview.date_last_updated == "2021-01-01T00:00:00.000Z"
    assert resource_preview.public
    assert resource_preview.discoverable
    assert resource_preview.shareable
    assert not resource_preview.immutable
    assert not resource_preview.published
    assert resource_preview.resource_url == "http://beta.hydroshare.org/resource/97523bdb7b174901b3fc2d89813458f1/"
    assert resource_preview.resource_map_url == "http://beta.hydroshare.org/resource/97523bdb7b174901b3fc2d89813458f1/map/"
    assert resource_preview.science_metadata_url == "http://beta.hydroshare.org/resource/97523bdb7b174901b3fc2d89813458f1/science-metadata/"
    # check the optional fields
    assert resource_preview.abstract is None
    assert resource_preview.authors == []
    assert resource_preview.doi is None
    assert resource_preview.coverages == []


def test_user_info(user):
    assert user.name == "Castronova, Anthony M."
    assert user.email == "castronova.anthony@gmail.com"
    assert str(user.url) == "http://beta.hydroshare.org/user/11/"
    assert user.phone == "3399334127"
    assert user.address == "MA, US"
    assert user.organization == "CUAHSI"
    assert str(user.website) == "http://anthonycastronova.com/"
    assert str(user.identifiers[UserIdentifierType.ORCID]) == "https://orcid.org/0000-0002-1341-5681"
    assert str(user.identifiers[UserIdentifierType.research_gate_id]) == "https://www.researchgate.net/profile/Anthony_Castronova"
    assert str(user.identifiers[UserIdentifierType.google_scholar_id]) == "https://scholar.google.com/citations?user=ScWTFoQAAAAJ&hl=en"

    assert user.type == "Commercial/Professional"
    assert user.date_joined == parser.parse("2015-06-03T16:09:31.636Z")
    assert user.subject_areas == [
        "Hydrology",
        "Hydroinformatics",
        "Hydrologic Modeling",
        "Cloud-computing",
        "Reproducible Science",
    ]

    creator = Creator.from_user(user)
    assert creator.name == user.name
    assert creator.phone == user.phone
    assert creator.address == user.address
    assert creator.organization == user.organization
    assert creator.email == user.email
    assert creator.homepage == user.website
    assert creator.identifiers == user.identifiers
    assert creator.hydroshare_user_id == int(user.url.path.split("/")[-2])

    contributor = Contributor.from_user(user)
    assert contributor.name == user.name
    assert contributor.phone == user.phone
    assert contributor.address == user.address
    assert contributor.organization == user.organization
    assert contributor.email == user.email
    assert contributor.homepage == user.website
    assert contributor.identifiers == user.identifiers
    assert contributor.hydroshare_user_id == int(user.url.path.split("/")[-2])
