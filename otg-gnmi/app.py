# app.py
from concurrent import futures
import grpc
import argparse

from .autogen import gnmi_pb2_grpc
from .gnmi_serv import GnmiService


class Server:

    @staticmethod
    def run(args):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        gnmi_pb2_grpc.add_gNMIServicer_to_server(GnmiService(args), server)
        server_address = "[::]:{}".format(args.server_port)
        app_name = "Athena"
        if (app_mode == 'ixnetwork'):
            app_name = 'IxNetwork'        
        server.add_insecure_port(server_address)
        logging.info("Starting gNMI server on %s [App: %s, Target: %s:%s]", server_address, args.app_name, args.target_host, args.target_port)
        server.start()

        def handle_sigterm(*_):
            print("Server received shutdown signal")
            all_rpcs_done_event = server.stop(30)
            all_rpcs_done_event.wait(30)
            print("Server shutdown gracefully")

        signal(SIGTERM, handle_sigterm)
        server.wait_for_termination()    
