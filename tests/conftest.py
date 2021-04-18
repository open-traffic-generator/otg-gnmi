# conftest.py
import pytest
import sys
import subprocess
import time
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
            "50055",
            "--unittest",
            "True",
            "--app-mode",
            "athena"
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
    """Demonstrates creating a top level Api instance.
    """
    snappiserver = subprocess.Popen(
        [
            "python",
            "-m",
            "tests.snappiserver",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # Give the server time to start
    time.sleep(2) 
    yield snappiserver
    # Shut it down at the end of the pytest session
    snappiserver.terminate()

@pytest.fixture(scope="session")
def session():    
    from tests.session import Session
    session = Session()
    session.options.waitForResponses = 10
    return session
