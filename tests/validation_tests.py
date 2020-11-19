from datetime import datetime

import pytest
from pydantic.error_wrappers import ValidationError

from hs_rdf.namespaces import DCTERMS
from hs_rdf.schemas import load_rdf
from hs_rdf.schemas.enums import VariableType
from hs_rdf.schemas.fields import ExtendedMetadata, Date, DateType, Variable, Coverage, PointCoverage


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


def test_variables():
    variable = Variable(name="name", type=VariableType.Byte, unit="unit", shape="shape",
                        descriptive_name="descriptive_name", method="method", missing_value="missing_value")
    assert variable.name == "name"
    assert variable.type == VariableType.Byte
    assert variable.unit == "unit"
    assert variable.shape == "shape"
    assert variable.descriptive_name == "descriptive_name"
    assert variable.method == "method"
    assert variable.missing_value == "missing_value"

    try:
        Variable()
        assert False, "Some Variable fields should be required"
    except ValidationError as ve:
        assert "4 validation errors for Variable" in str(ve)
        assert "name" in str(ve)
        assert "unit" in str(ve)
        assert "type" in str(ve)
        assert "shape" in str(ve)


def test_one_spatial_coverage(res_md):
    coverages = res_md.coverages
    point_coverage = PointCoverage(name="Logan River Watershed", east=-111.833736, north=41.710961,
                                   units="Decimal degrees", projection="WGS 84 EPSG:4326")
    coverages.append(Coverage(type=point_coverage.type, value=point_coverage))
    try:
        res_md.coverages = coverages
        assert False, "Only one type of spatial coverage should be allowed"
    except ValueError as ve:
        assert "Only one type of spatial coverage is allowed, point or box" in str(ve)
