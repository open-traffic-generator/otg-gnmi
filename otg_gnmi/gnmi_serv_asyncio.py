# gnmi_serv_asyncio.py

import datetime
import logging

import grpc

from .autogen import gnmi_pb2, gnmi_pb2_grpc
from .common.ixnutils import TestManager
from .common.utils import (get_subscription_mode_string, get_time_elapsed,
                           init_logging)


class ServerOptions(object):
    def __init__(self, args):
        self.app_mode = args.app_mode
        self.unittest = args.unittest
        self.logfile = args.logfile
        self.target_address = "{}:{}".format(
            args.target_host, args.target_port)
        self.no_stdout = args.no_stdout
        self.log_level = logging.DEBUG


class AsyncGnmiService(gnmi_pb2_grpc.gNMIServicer):

    def __init__(self, args):
        super().__init__()
        self.options = ServerOptions(args)
        log_stdout = not self.options.no_stdout

        self.logger = init_logging(
            'gnmi',
            'gnmi_serv_asyncio',
            self.options.logfile,
            self.options.log_level,
            log_stdout
        )

        self.profile_logger = init_logging(
            'profile',
            'gnmi_serv_asyncio',
            self.options.logfile,
            self.options.log_level,
            log_stdout
        )
        self.target_address = "{}:{}".format(
            args.target_host, args.target_port)

    async def Capabilities(self, request, context):
        """Capabilities allows the client to retrieve the set of capabilities that
        is supported by the target. This allows the target to validate the
        service version that is implemented and retrieve the set of models that
        the target supports. The models can then be specified in subsequent RPCs
        to restrict the set of data that is utilized.
        Reference: gNMI Specification Section 3.2
        """ # noqa
        get_capabilities_start = datetime.datetime.now()
        try:
            response = await TestManager.Instance().get_supported_models()
            context.set_code(grpc.StatusCode.OK)
            context.set_details('Success!')
            return response
        finally:
            self.profile_logger.info(
                "Capabilities completed!", extra={
                    'nanoseconds':  get_time_elapsed(get_capabilities_start)
                }
            )

    async def Get(self, request, context):
        """Retrieve a snapshot of data from the target. A Get RPC requests that the
        target snapshots a subset of the data tree as specified by the paths
        included in the message and serializes this to be returned to the
        client using the specified encoding.
        Reference: gNMI Specification Section 3.3
        """
        get_start = datetime.datetime.now()
        try:
            context.set_code(grpc.StatusCode.UNIMPLEMENTED)
            context.set_details('Method not implemented!')
            raise NotImplementedError('Method not implemented!')
        finally:
            self.profile_logger.info(
                "Get completed!", extra={
                    'nanoseconds':  get_time_elapsed(get_start)
                }
            )

    async def Set(self, request, context):
        """Set allows the client to modify the state of data on the target. The
        paths to modified along with the new values that the client wishes
        to set the value to.
        Reference: gNMI Specification Section 3.4
        """
        set_start = datetime.datetime.now()
        try:
            context.set_code(grpc.StatusCode.UNIMPLEMENTED)
            context.set_details('Method not implemented!')
            raise NotImplementedError('Method not implemented!')
        finally:
            self.profile_logger.info(
                "Set completed!", extra={
                    'nanoseconds':  get_time_elapsed(set_start)
                }
            )

    async def Subscribe(self, request_iterator, context):
        """Subscribe allows a client to request the target to send it values
        of particular paths within the data tree. These values may be streamed
        at a particular cadence (STREAM), sent one off on a long-lived channel
        (POLL), or sent as a one-off retrieval (ONCE).
        Reference: gNMI Specification Section 3.5
        """
        subscribe_start = datetime.datetime.now()
        try:
            self.logger.info(
                'Received subscription request. Metadata: %s',
                context.invocation_metadata()
            )
            self.logger.info(
                'Received subscription request. Peer %s, Peer Identities %s',
                context.peer(),
                context.peer_identities()
            )

            init, error = await TestManager.Instance().init_once_func(
                self.options)
            if init is False:
                context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                context.set_details(error)
                raise Exception(error)

            session = await TestManager.Instance().create_session(
                context,
                request_iterator
            )
            # https://github.com/grpc/grpc/issues/23070
            # context.add_done_callback(TestManager.Instance().terminate(request_iterator))
            await TestManager.Instance().register_subscription(session)
            self.logger.info(
                'Starting polling stats for mode : %s',
                get_subscription_mode_string(session.mode))
            error = False
            counter = 0
            while await TestManager.Instance().keep_polling():

                try:
                    responses = await TestManager.Instance().publish_stats(
                        session)
                    for response in responses:
                        if response is not None:
                            self.logger.info(
                                'Response[%s]: %s', counter, response)
                            yield response
                    counter = counter + 1
                    if (
                        session.mode == gnmi_pb2.SubscriptionList.Mode.ONCE or
                        session.mode == gnmi_pb2.SubscriptionList.Mode.POLL
                        ) and \
                            session.sent_sync is True:
                        self.logger.info(
                            'Completed for %s, sync sent %s',
                            get_subscription_mode_string(session.mode),
                            session.sent_sync
                        )
                        break

                except BaseException as innerEx:
                    self.logger.error('Exception: %s', str(innerEx))
                    self.logger.error(
                        'Connection closed. Peer %s', context.peer())
                    error = True
                if error:
                    break

            await TestManager.Instance().deregister_subscription(session)
            await TestManager.Instance().remove_session(context)

            context.set_code(grpc.StatusCode.OK)
            context.set_details('Success!')

        finally:
            self.profile_logger.info(
                "Subscribe completed!", extra={
                    'nanoseconds':  get_time_elapsed(subscribe_start)
                }
            )
