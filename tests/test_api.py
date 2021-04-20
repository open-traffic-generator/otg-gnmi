import pytest
from tests.conftest import *

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
    result = session.subscribe()
    assert(result == True)
