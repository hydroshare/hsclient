from datetime import datetime, timedelta

import pytest
from pydantic.error_wrappers import ValidationError

from hs_rdf.namespaces import DCTERMS
from hs_rdf.schemas import load_rdf
from hs_rdf.schemas.data_structures import PeriodCoverage, BoxCoverage
from hs_rdf.schemas.enums import VariableType
from hs_rdf.schemas.fields import ExtendedMetadataInRDF, DateInRDF, DateType, Variable, Rights, Creator


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


def test_extended_metadata():
    em = ExtendedMetadataInRDF(key='key1', value='value1')
    assert em.key == 'key1'
    assert em.value == 'value1'
    try:
        ExtendedMetadataInRDF()
        assert False, "ExtendedMetadata key/value are required"
    except ValueError as ve:
        assert "field required" in str(ve)

def test_dates():
    now = datetime.now()
    d = DateInRDF(type=str(DCTERMS.modified), value=now)
    assert d.type == DateType.modified
    assert d.value == now
    try:
        DateInRDF()
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

def test_rights():
    assert Rights.Creative_Commons_Attribution_CC_BY() == \
           Rights(statement="This resource is shared under the Creative Commons Attribution CC BY.",
                  url="http://creativecommons.org/licenses/by/4.0/")

    assert Rights.Creative_Commons_Attribution_ShareAlike_CC_BY() == \
           Rights(statement="This resource is shared under the Creative Commons Attribution-ShareAlike CC BY-SA.",
                  url="http://creativecommons.org/licenses/by-sa/4.0/")

    assert Rights.Creative_Commons_Attribution_NoDerivs_CC_BY_ND() == \
           Rights(statement="This resource is shared under the Creative Commons Attribution-ShareAlike CC BY-SA.",
                  url="http://creativecommons.org/licenses/by-nd/4.0/")

    assert Rights.Creative_Commons_Attribution_NoCommercial_ShareAlike_CC_BY_NC_SA() == \
           Rights(statement="This resource is shared under the Creative Commons Attribution-NoCommercial-ShareAlike"
                            " CC BY-NC-SA.",
                  url="http://creativecommons.org/licenses/by-nc-sa/4.0/")

    assert Rights.Creative_Commons_Attribution_NoCommercial_CC_BY_NC() == \
           Rights(statement="This resource is shared under the Creative Commons Attribution-NoCommercial CC BY-NC.",
                  url="http://creativecommons.org/licenses/by-nc/4.0/")

    assert Rights.Creative_Commons_Attribution_NoCommercial_NoDerivs_CC_BY_NC_ND() == \
           Rights(statement="This resource is shared under the Creative Commons Attribution-NoCommercial-NoDerivs "
                            "CC BY-NC-ND.",
                  url="http://creativecommons.org/licenses/by-nc-nd/4.0/")

    assert Rights.Other("a statement", "https://www.hydroshare.org") == \
           Rights(statement="a statement", url="https://www.hydroshare.org")

def test_period_constraints_error():
    start = datetime.now()
    end = datetime.now() - timedelta(seconds=1)
    try:
        PeriodCoverage(start=start, end=end)
        assert False, "Should have raised error"
    except ValueError as e:
        assert f"start date [{start}] is after end date [{end}]" in str(e)

def test_period_constraint_happy_path():
    start = datetime.now()
    end = datetime.now() + timedelta(seconds=1)
    pc = PeriodCoverage(name="hello", start=start, end=end)
    assert pc.start == start
    assert pc.end == end
    assert pc.name == "hello"

def test_box_constraints_north_south():
    box_coverage = BoxCoverage(name="asdfsadf", northlimit=42.1505, eastlimit=-84.5739,
                               projection='WGS 84 EPSG:4326', southlimit=30.282,
                               units='Decimal Degrees', westlimit=-104.7887)

    try:
        box_coverage.northlimit = 29
        assert False, "Should have thrown error"
    except ValueError as e:
        assert "North latitude [29.0] must be greater than or equal to South latitude [30.282]" in str(e)

def test_invalid_email():
    try:
        creator = Creator(email="bad")
        assert False, "Should have thrown error"
    except ValueError as e:
        assert "value is not a valid email address" in str(e)

