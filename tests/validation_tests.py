from datetime import datetime

import pytest
from pydantic.error_wrappers import ValidationError

from hs_rdf.namespaces import DCTERMS
from hs_rdf.schemas import load_rdf
from hs_rdf.schemas.fields import ExtendedMetadata, Date, DateType


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

def test_extended_metadata():
    em = ExtendedMetadata(key='key1', value='value1')
    assert em.key == 'key1'
    assert em.value == 'value1'
    try:
        ExtendedMetadata()
        assert False, "ExtendedMetadata key/value are required"
    except ValueError as ve:
        assert "field required" in str(ve)

def test_dates():
    now = datetime.now()
    d = Date(type=str(DCTERMS.modified), value=now)
    assert d.type == DateType.modified
    assert d.value == now
    try:
        Date()
        assert False, "Date type/value are required"
    except ValidationError as ve:
        assert "2 validation errors for Date" in str(ve)
