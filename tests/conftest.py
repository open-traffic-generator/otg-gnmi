# conftest.py
import pytest
import sys
import subprocess
import time
from otg_gnmi.common.ixnutils import *
sys.path.append('.')


'''
@pytest.fixture(scope='module')
def grpc_add_to_server():
    from otg_gnmi.autogen.gnmi_pb2_grpc import add_gNMIServicer_to_server
    
    return add_gNMIServicer_to_server


@pytest.fixture(scope='module')
def grpc_servicer():
    from otg_gnmi.autogen.gnmi_pb2_grpc import gNMIServicer
    
    return gNMIServicer()


@pytest.fixture(scope='module')
def grpc_stub(grpc_channel):
    from otg_gnmi.autogen.gnmi_pb2_grpc import gNMIStub

    return gNMIStub(grpc_channel)
'''

@pytest.fixture(scope='module')
def gnmi_server():
    gnmi_server = subprocess.Popen(
        [
            "python",
            "-m",
            "otg_gnmi",
            "--server-port",
            "50051",
            "--app-mode",
            "athena-insecure",
            "--target-host",
            "127.0.0.1",
            "--target-port",
            "11009",
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
    snappi_server_obj =  SnappiServer()
    pytest.snappiserver = snappi_server_obj.start()
    yield
    snappi_server_obj.stop()
    TestManager.Instance().stop_worker_threads()

@pytest.fixture(scope="session")
def session():    
    from tests.unit_gnmi_clinet.session import Session
    session = Session()
    session.options.waitForResponses = 3
    return session

