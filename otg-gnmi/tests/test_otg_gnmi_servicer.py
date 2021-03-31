import grpc
import pytest
from grpc_mate.gnmi_pb2 import HelloRequest


@pytest.fixture(scope='module')
def grpc_add_to_server():
    from grpc_mate.gnmi_pb2_grpc import add_gNMIServicer_to_server

    return add_gNMIServicer_to_server


@pytest.fixture(scope='module')
def grpc_servicer():
    from service.greeter_servicer import gNMIServicer

    return gNMIServicer()


@pytest.fixture(scope='module')
def grpc_stub_cls(grpc_channel):
    from grpc_mate.gnmi_pb2_grpc import gNMIStub

    return gNMIStub


def test_SayHello(grpc_stub):
    hello_request = HelloRequest(name='ivan')
    response = grpc_stub.SayHello(hello_request)

    assert response.message == f'hello {hello_request.name}'


def integration_test_Subscribe():
    from grpc_mate.gnmi_pb2_grpc import gNMIStub
    channel = grpc.insecure_channel('localhost:8080')
    stub = gNMIStub(channel)
    hello_request = HelloRequest(name='local')
    response = stub.Subscribe(hello_request)
    assert response.message == f'hello {hello_request.name}'