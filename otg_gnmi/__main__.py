# __main__.py
import argparse
import asyncio

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
                        default=11020,
                        type=int)
    parser.add_argument('--unittest', help='set to true if running unit test',
                        action='store_true')
    parser.add_argument('--logfile',
                        help='logfile name [date and time auto appended]',
                        default='gNMIServer',
                        type=str)
    parser.add_argument('--no-stdout',
                        help='do not show log on stdout',
                        default=False,
                        action='store_true')
    parser.add_argument('--insecure',
                        help='disable TSL security, by default enabled',
                        action='store_true')
    parser.add_argument('--server-key',
                        help='path to private key, default is server.key',
                        default='server.key',
                        type=str)
    parser.add_argument('--server-crt',
                        help='path to certificate key, default is server.crt',
                        default='server.crt',
                        type=str)
    args = parser.parse_args()

    asyncio.run(AsyncServer.run(args))
