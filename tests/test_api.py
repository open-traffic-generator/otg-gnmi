import pytest
from tests.conftest import *

def test_capabilites(gnmi_server, snappiserver, session):
    resp = session.capabilites()

def test_get(gnmi_server, snappiserver, session):
    resp = session.get()

def test_set(gnmi_server, snappiserver, session):
    session.set()

def test_subscribe(gnmi_server, snappiserver, session):
    session.subscribe()
