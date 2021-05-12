# app.py
from concurrent import futures
import grpc
import grpc.experimental.aio as grpc_async
from grpc_reflection.v1alpha import reflection
import asyncio
import logging
import argparse
import os

from .autogen import gnmi_pb2_grpc
from .common.ixnutils import *
from .common.utils import *
from .gnmi_serv_asyncio import AsyncGnmiService


class AsyncServer:

    @staticmethod
    async def run(args) -> None:              
        #https://github.com/grpc/grpc/issues/23070  
        args.logfile = init_logging(args.logfile)
        server_logger = logging.getLogger(args.logfile) 

        grpc_async.init_grpc_aio()
        server = grpc.aio.server()
        gnmi_pb2_grpc.add_gNMIServicer_to_server(AsyncGnmiService(args), server)
        SERVICE_NAMES = (
            gnmi_pb2.DESCRIPTOR.services_by_name['gNMI'].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(SERVICE_NAMES, server)

        
        
        server_address = "[::]:{}".format(args.server_port)
        app_name = "Athena"
        if args.app_mode == 'ixnetwork':
            app_name = 'IxNetwork'        
        if args.insecure == True:
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

            if private_key != None and certificate_chain != None:
                server_credentials = grpc.ssl_server_credentials( ( (private_key, certificate_chain), ) )
                server.add_secure_port(server_address, server_credentials)
                server_logger.info("Enabled secure channel")
            else:
                server_logger.error("Cannot create secure channel, need openssl key. You can generate it with below openssl command")
                server_logger.error("openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt -subj '/CN=test.local'")
            
        server_logger.info("Starting gNMI server on %s [App: %s, Target: %s:%s]", server_address, app_name, args.target_host, args.target_port)
        
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
            all_rpcs_done_event.wait(30)
            print("Server shutdown gracefully")            
            