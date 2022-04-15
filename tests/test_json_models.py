import json
import os

import pytest
from dateutil import parser
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


AuthorsFieldResourcePreviewTestData = (
    json.dumps({"authors": None}),
    json.dumps({"authors": []}),
    json.dumps({"authors": [None]}),
    json.dumps({"authors": [""]}),
    json.dumps({"authors": [[]]}),
)


@pytest.mark.parametrize("test_data", AuthorsFieldResourcePreviewTestData)
def test_resource_preview_authors_field_handles_none_cases(test_data):
    """verify all `authors` fields are instantiated with [] values.

    coerced `authors` field should be [] with following input:
        None
        []
        [None]
        [None, ""]
    """

    from_json = ResourcePreview.parse_raw(test_data)

    assert from_json.authors == []


def test_resource_preview_authors_raises_validation_error_on_string_input():
    """verify that a string passed to authors field raises pydantic.ValidationError"""
    from pydantic import ValidationError

    data = json.dumps({"authors": "should_fail"})

    with pytest.raises(ValidationError):
        ResourcePreview.parse_raw(data)


def test_user_info(user):
    assert user.name == "Castronova, Anthony M."
    assert user.email == "castronova.anthony@gmail.com"
    assert user.url == "http://beta.hydroshare.org/user/11/"
    assert user.phone == "3399334127"
    assert user.address == "MA, US"
    assert user.organization == "CUAHSI"
    assert user.website == "http://anthonycastronova.com"
    assert user.identifiers == {
        "ORCID": "https://orcid.org/0000-0002-1341-5681",
        "ResearchGateID": "https://www.researchgate.net/profile/Anthony_Castronova",
        "GoogleScholarID": "https://scholar.google.com/citations?user=ScWTFoQAAAAJ&hl=en",
    }
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
    assert creator.description == user.url.path

    contributor = Contributor.from_user(user)
    assert contributor.name == user.name
    assert contributor.phone == user.phone
    assert contributor.address == user.address
    assert contributor.organization == user.organization
    assert contributor.email == user.email
    assert contributor.homepage == user.website
    assert contributor.identifiers == user.identifiers
