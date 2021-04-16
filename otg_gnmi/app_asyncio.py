# app.py
from concurrent import futures
import grpc
import grpc.experimental.aio as grpc_async
import asyncio
import logging
import argparse

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
        
        server_address = "[::]:{}".format(args.server_port)
        app_name = "Athena"
        if (args.app_mode == 'ixnetwork'):
            app_name = 'IxNetwork'        
        server.add_insecure_port(server_address)
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
            