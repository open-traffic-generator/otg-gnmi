# conftest.py
import pytest
import sys
import subprocess
import time
from otg_gnmi.common.ixnutils import TestManager
sys.path.append('.')


@pytest.fixture(scope='module')
def gnmi_server():
    gnmi_server = subprocess.Popen(
        [
            "python",
            "-m",
            "otg_gnmi",
            "--server-port",
            "50052",
            "--app-mode",
            "athena",
            "--unittest",
            "--insecure"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # Give the server time to start
    time.sleep(2)
    yield gnmi_server
    # Shut it down at the end of the pytest session
    # Give the server time to flush any pending request
    time.sleep(2)
    gnmi_server.terminate()


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


@pytest.fixture(scope="session")
def session():
    from tests.session import Session
    session = Session()
    session.options.waitForResponses = 3
    return session
