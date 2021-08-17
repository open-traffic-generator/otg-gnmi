import pytest
from tests.conftest import *
from tests.utils.common import *

def test_capabilites(gnmi_server, snappiserver, session):
    result = session.capabilites()
    assert(result == True)

def test_get(gnmi_server, snappiserver, session):
    result = session.get()
    assert(result == False)

def test_set(gnmi_server, snappiserver, session):
    result = session.set()
    assert(result == False)

def test_subscribe(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.subscribe()
    assert(result == True)
