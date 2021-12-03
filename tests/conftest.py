# conftest.py
import sys

import pytest
from otg_gnmi.common.ixnutils import TestManager

sys.path.append('.')


@pytest.fixture(scope='session')
def snappiserver():
    """Demonstrates creating Mock Snappi Servers.
    """
    from .snappiserver import SnappiServer
    snappi_server_obj = SnappiServer()
    pytest.snappiserver = snappi_server_obj.start()
    yield
    snappi_server_obj.stop()
    TestManager.Instance().stop_worker_threads()
