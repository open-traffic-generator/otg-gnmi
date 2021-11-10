# conftest.py
import subprocess
import sys
import time

import pytest
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
            "50090",
            "--app-mode",
            "athena",
            "--unittest",
            "--insecure",
            "--no-stdout"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # Give the server time to start
    time.sleep(2)
    yield gnmi_server
    # Shut it down at the end of the pytest session
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
