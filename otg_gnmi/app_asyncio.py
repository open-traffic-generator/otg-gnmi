# app_asyncio.py
import logging
import signal

import grpc
import grpc.experimental.aio as grpc_async
from grpc_reflection.v1alpha import reflection

from .autogen import gnmi_pb2, gnmi_pb2_grpc
from .common.ixnutils import TestManager
from .common.utils import init_logging, get_current_time
from .gnmi_serv_asyncio import AsyncGnmiService

server = None


class AsyncServer:

    @staticmethod
    async def run(args) -> None:
        global server

        # https://github.com/grpc/grpc/issues/23070
        log_stdout = not args.no_stdout
        args.logfile = args.logfile+'-'+str(get_current_time())+'.log'
        server_logger = init_logging(
            'gnmi',
            'app_asyncio',
            args.logfile,
            logging.DEBUG,
            log_stdout
        )
        signal.signal(signal.SIGTERM, sighandler)

        grpc_async.init_grpc_aio()
        server = grpc.aio.server()
        gnmi_pb2_grpc.add_gNMIServicer_to_server(
            AsyncGnmiService(args), server)
        SERVICE_NAMES = (
            gnmi_pb2.DESCRIPTOR.services_by_name['gNMI'].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(SERVICE_NAMES, server)

        server_address = "[::]:{}".format(args.server_port)
        app_name = "Athena"
        if args.app_mode == 'ixnetwork':
            app_name = 'IxNetwork'
        if args.insecure is True:
            server_logger.info("Enabling insecure channel")
            server.add_insecure_port(server_address)
            server_logger.info("Enabled insecure channel")
        else:
            server_logger.info("Enabling secure channel")
            private_key = None
            certificate_chain = None
            with open(args.server_key, 'rb') as f:
                private_key = f.read()
            with open(args.server_crt, 'rb') as f:
                certificate_chain = f.read()

            if private_key is not None and certificate_chain is not None:
                server_credentials = grpc.ssl_server_credentials(
                    ((private_key, certificate_chain), ))
                server.add_secure_port(server_address, server_credentials)
                server_logger.info("Enabled secure channel")
            else:
                server_logger.error(
                    "Cannot create secure channel, need openssl key. You can generate it with below openssl command" # noqa
                )
                server_logger.error(
                    "openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt -subj '/CN=test.local'" # noqa
                )

        server_logger.info(
            "Starting gNMI server on %s [App: %s, Target: %s:%s]",
            server_address, app_name,
            args.target_host,
            args.target_port
        )

        await server.start()

        try:
            await server.wait_for_termination()
        except KeyboardInterrupt:
            # Shuts down the server with 0 seconds of grace period. During the
            # grace period, the server won't accept new connections and allow
            # existing RPCs to continue within the grace period.
            server_logger.info('Stopping async server')
            TestManager.Instance().terminate()
            all_rpcs_done_event = await server.stop(5)
            server = None
            all_rpcs_done_event.wait(30)
            print("Server shutdown gracefully")


def sighandler(signum, frame):
    global server

    if server is not None:
        TestManager.Instance().terminate()
        server.stop(5)
        server = None
        print("Server shutdown gracefully")
