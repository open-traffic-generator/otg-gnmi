
import grpc
from .autogen import gnmi_pb2_grpc, gnmi_pb2
#from .common.utils import *


class GnmiService(gnmi_pb2_grpc.gNMIServicer):

  def __init__(self, args):
    super().__init__()

    self.app_mode = args.app_mode
    self.target_address = "{}:{}".format(args.target_host, args.target_port)    
    
  def Capabilities(self, request, context):
    """Capabilities allows the client to retrieve the set of capabilities that
    is supported by the target. This allows the target to validate the
    service version that is implemented and retrieve the set of models that
    the target supports. The models can then be specified in subsequent RPCs
    to restrict the set of data that is utilized.
    Reference: gNMI Specification Section 3.2
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def Get(self, request, context):
    """Retrieve a snapshot of data from the target. A Get RPC requests that the
    target snapshots a subset of the data tree as specified by the paths
    included in the message and serializes this to be returned to the
    client using the specified encoding.
    Reference: gNMI Specification Section 3.3
    """
    TestManager.Instance().setup_test()
    result = TestManager.Instance().get_metrics()
    return result

  def Set(self, request, context):
    """Set allows the client to modify the state of data on the target. The
    paths to modified along with the new values that the client wishes
    to set the value to.
    Reference: gNMI Specification Section 3.4
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def Subscribe(self, request_iterator, context):
    """Subscribe allows a client to request the target to send it values
    of particular paths within the data tree. These values may be streamed
    at a particular cadence (STREAM), sent one off on a long-lived channel
    (POLL), or sent as a one-off retrieval (ONCE).
    Reference: gNMI Specification Section 3.5
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

