# __main__.py
from .app import Server
from .app_asyncio import AsyncServer
import asyncio
import logging
import datetime
import argparse
import os

USE_ASYNC = True

def get_current_time():
    current_utc = datetime.datetime.utcnow()
    current_utc = str(current_utc).split('.')[0]
    current_utc = current_utc.replace(' ','-')
    current_utc = current_utc.replace(':','-')
    return current_utc

def init_logging():
    logs_dir = os.path.join(os.path.curdir, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    logfile = 'gNMIService-'+str(get_current_time())+'.log'
    logfile = os.path.join(logs_dir, logfile)  
    logging.basicConfig(
        filename=logfile, 
        level=logging.INFO,
        format='%(asctime)s %(message)s', 
        datefmt='%m/%d/%Y %I:%M:%S %p')

if __name__ == '__main__':
    
    init_logging()

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--server-port', help='gRPC server port number',
                        default=40051,
                        type=int)
    parser.add_argument('--app-mode', help='target Application mode)',
                        choices=['ixnetwork', 'athena'],
                        default='ixnetwork',
                        type=str)
    parser.add_argument('--target-host', help='target host address',
                        default='localhost',
                        type=str)
    parser.add_argument('--target-port', help='target port number',
                        default=11009,
                        type=int)
    args = parser.parse_args()

    if USE_ASYNC:        
        asyncio.run(AsyncServer.run(args))
    else:
        Server.run(args)
        