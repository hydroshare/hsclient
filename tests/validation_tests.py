import pytest
from hs_rdf.schemas import load_rdf


@pytest.fixture()
def res_md():
    with open("data/metadata/resourcemetadata.xml", 'r') as f:
        return load_rdf(f.read())

def test_resource_metadata_language(res_md):
    try:
        res_md.language = "badcode"
        assert False, "language validator must not be working"
    except ValueError as ve:
        assert "language 'badcode' must be a 3 letter iso language code" in str(ve)

def test_resource_metadata_identifier(res_md):
    try:
        id = res_md.identifier
        id.hydroshare_identifier = "http://blah.com"
        res_md.identifier = id
        assert False, "identifier validator must not be working"
    except ValueError as ve:
        assert "rdf_subject and identifier.hydroshare_identifier must match" in str(ve)
