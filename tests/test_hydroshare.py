import json
from io import StringIO

import pytest
import requests

from hs_rdf.implementations.hydroshare import HydroShare, Resource


def test_auth(monkeypatch):
    hs = HydroShare("test_username", "test_password")
    assert hs._hs_session._session.auth == ("test_username", "test_password")

def test_signin(monkeypatch):
    monkeypatch.setattr('sys.stdin', StringIO("test_username"))
    monkeypatch.setattr('getpass.getpass', lambda x: "test_password")
    hs = HydroShare()
    hs.sign_in()
    assert hs._hs_session._session.auth == ("test_username", "test_password")

def test_search():
    pass

def test_resource():
    hs = HydroShare("user", "pass")
    res = hs.resource("39ec2bee16614f96a1d41b0916c72258")

    assert isinstance(res, Resource)
    assert res._map_url == "https://dev-hs-1.cuahsi.org/resource/39ec2bee16614f96a1d41b0916c72258/data/resourcemap.xml"
    assert res._hs_session == hs._hs_session

def test_create(requests_mock):
    requests_mock.post("https://dev-hs-1.cuahsi.org/hsapi/resource/", text=json.dumps({'resource_id': "new_resource_id"}))

    hs = HydroShare("user", "pass")
    res = hs.create()

    assert isinstance(res, Resource)
    assert res._map_url == "https://dev-hs-1.cuahsi.org/resource/new_resource_id/data/resourcemap.xml"
    assert res._hs_session == hs._hs_session
