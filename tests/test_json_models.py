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


def test_resource_preview_authors_field_default_is_empty_list():
    """verify all `authors` fields are instantiated with [] values."""
    test_data_dict = {"authors": None}
    test_data_json = '{"authors": null}'

    base_case = ResourcePreview()
    from_kwargs = ResourcePreview(**test_data_dict)
    from_dict = ResourcePreview.parse_obj(test_data_dict)
    from_json = ResourcePreview.parse_raw(test_data_json)

    assert all([x.authors == [] for x in [base_case, from_kwargs, from_dict, from_json]])


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
    assert creator.hydroshare_user_id == user.id

    contributor = Contributor.from_user(user)
    assert contributor.name == user.name
    assert contributor.phone == user.phone
    assert contributor.address == user.address
    assert contributor.organization == user.organization
    assert contributor.email == user.email
    assert contributor.homepage == user.website
    assert contributor.identifiers == user.identifiers
    assert contributor.hydroshare_user_id == user.id
