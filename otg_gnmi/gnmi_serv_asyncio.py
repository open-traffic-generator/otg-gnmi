import asyncio
import grpc
import time
import logging
from .autogen import gnmi_pb2_grpc, gnmi_pb2
from .common.ixnutils import *
from .common.utils import *
from .common.client_session import *

class ServerOptions(object):
  def __init__(self, args):
    self.app_mode = args.app_mode
    self.unittest = args.unittest
    self.logfile = args.logfile
    self.target_address = "{}:{}".format(args.target_host, args.target_port)
    
class AsyncGnmiService(gnmi_pb2_grpc.gNMIServicer):

  def __init__(self, args):
      super().__init__()
      self.options = ServerOptions(args)
      self.logger = logging.getLogger(self.options.logfile)
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
    
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')
    
    '''
    self.logger.info("Received set request. Metadata: %s", context.invocation_metadata())
    self.logger.info("Received set request. Peer %s, Peer Identities %s", context.peer(), context.peer_identities())
    
    try:
      init, error = await TestManager.Instance().init_once_func(self.options)
      if init == False:
        context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
        context.set_details(error)
        raise Exception(error)
    except Exception as ex:
      #await TestManager.Instance().terminate(request_iterator)
      self.logger.error('Exception: %s', str(ex))
      self.logger.error('Exception: ', exc_info=True)

    return request
    '''

  async def Subscribe(self, request_iterator, context):
    """Subscribe allows a client to request the target to send it values
    of particular paths within the data tree. These values may be streamed
    at a particular cadence (STREAM), sent one off on a long-lived channel
    (POLL), or sent as a one-off retrieval (ONCE).
    Reference: gNMI Specification Section 3.5
    """

      
    self.logger.info("Received subscription request. Metadata: %s", context.invocation_metadata())
    self.logger.info("Received subscription request. Peer %s, Peer Identities %s", context.peer(), context.peer_identities())
    
    init, error = await TestManager.Instance().init_once_func(self.options)
    if init == False:
      context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
      context.set_details(error)
      raise Exception(error)
    
    session = await TestManager.Instance().create_new_session(context)
    # https://github.com/grpc/grpc/issues/23070
    #context.add_done_callback(TestManager.Instance().terminate(request_iterator))
    await TestManager.Instance().register_subscription(session, request_iterator)

    error = False
    while await TestManager.Instance().keep_polling():
          
      try:
        responses = await TestManager.Instance().publish_stats(session)
        for response in responses:
          if response != None:
            self.logger.info('Response: %s', response)
            yield response
      except Exception as innerEx:
        self.logger.error('Exception: %s', str(innerEx))
        self.logger.error('Exception: ', exc_info=True)
        error = True
      if error:
        break
      await asyncio.sleep(2)

    await TestManager.Instance().deregister_subscription(session, request_iterator)
      

