# __main__.py
import asyncio
import logging
import argparse

from .app_asyncio import AsyncServer


if __name__ == '__main__':
    
    

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--server-port', help='gRPC server port number',
                        default=50051,
                        type=int)
    parser.add_argument('--app-mode', help='target Application mode)',
                        choices=['ixnetwork', 'athena'],
                        default='ixnetwork',
                        type=str)
    parser.add_argument('--target-host', help='target host address',
                        default='localhost',
                        )
    parser.add_argument('--target-port', help='target port number',
                        default=11009,
                        type=int)
    parser.add_argument('--unittest', help='true if running unit test',
                        default=False,
                        type=bool)
    parser.add_argument('--logfile', help='logfile name [date and time auto appended]',
                        default='gNMIServer',
                        type=str)
    args = parser.parse_args()

    asyncio.run(AsyncServer.run(args))
        