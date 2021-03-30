import asyncio
import grpc
import time
import logging
from .autogen import gnmi_pb2_grpc, gnmi_pb2
from .common.ixnutils import *
from .common import gnmiutils


class AsyncGnmiService(gnmi_pb2_grpc.gNMIServicer):

  def __init__(self, args):
      super().__init__()
      self.app_mode = args.app_mode
      self.target_address = "{}:{}".format(args.target_host, args.target_port)
    
  async def Capabilities(self, request, context):
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

  async def Get(self, request, context):
    """Retrieve a snapshot of data from the target. A Get RPC requests that the
    target snapshots a subset of the data tree as specified by the paths
    included in the message and serializes this to be returned to the
    client using the specified encoding.
    Reference: gNMI Specification Section 3.3
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  async def Set(self, request, context):
    """Set allows the client to modify the state of data on the target. The
    paths to modified along with the new values that the client wishes
    to set the value to.
    Reference: gNMI Specification Section 3.4
    """
    '''
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')
    '''
    logging.info("Received set request. Metadata: %s", context.invocation_metadata())
    logging.info("Received set request. Peer %s, Peer Identities %s", context.peer(), context.peer_identities())
    
    try:
      init, error = await TestManager.Instance().init_once_func(self.app_mode, self.target_address)
      if init == False:
        context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
        context.set_details(error)
        raise Exception(error)
    except Exception as ex:
      #await TestManager.Instance().terminate(request_iterator)
      logging.error('Exception: %s', str(ex))
      logging.error('Exception: ', exc_info=True)

    return request

  async def Subscribe(self, request_iterator, context):
    """Subscribe allows a client to request the target to send it values
    of particular paths within the data tree. These values may be streamed
    at a particular cadence (STREAM), sent one off on a long-lived channel
    (POLL), or sent as a one-off retrieval (ONCE).
    Reference: gNMI Specification Section 3.5
    """

      
    logging.info("Received subscription request. Metadata: %s", context.invocation_metadata())
    logging.info("Received subscription request. Peer %s, Peer Identities %s", context.peer(), context.peer_identities())
    
    try:
      init, error = await TestManager.Instance().init_once_func(self.app_mode, self.target_address)
      if init == False:
        context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
        context.set_details(error)
        raise Exception(error)
      
      # https://github.com/grpc/grpc/issues/23070
      #context.add_done_callback(TestManager.Instance().terminate(request_iterator))
      await TestManager.Instance().register_subscription(request_iterator)

      while await TestManager.Instance().keep_polling():
            
        responses = await TestManager.Instance().publish_stats()
        for response in responses:
          if response != None:
            logging.info('Response: %s', response)
            yield response
        await asyncio.sleep(2)

    except Exception as ex:
      #await TestManager.Instance().terminate(request_iterator)
      logging.error('Exception: %s', str(ex))
      logging.error('Exception: ', exc_info=True)
      

