import os
import datetime
import logging
import json
import asyncio
import time
from enum import Enum
import re

from ..autogen import gnmi_pb2_grpc, gnmi_pb2


class RequestPathBase():
    BASE_PORT_PATH = r'/port_metrics'
    BASE_FLOW_PATH = r'/flow_metrics'
    BASE_BGPv4_PATH = r'/bgpv4_metrics'
    BASE_BGPv6_PATH = r'/bgpv6_metrics'


class RequestType(Enum):
    UNKNOWN = 0
    PORT = 1
    FLOW = 2
    PROTOCOL = 3


def get_current_time():
    current_utc = datetime.datetime.utcnow()
    current_utc = str(current_utc).split('.')[0]
    current_utc = current_utc.replace(' ', '-')
    current_utc = current_utc.replace(':', '-')
    return current_utc


'''
def init_logging(name):
    logs_dir = os.path.join(os.path.curdir, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    logfile = name+'-'+str(get_current_time())+'.log'
    logfile = os.path.join(logs_dir, logfile)  
    logging.basicConfig(
        filename=logfile, 
        level=logging.INFO,
        format='%(asctime)s %(message)s', 
        datefmt='%m/%d/%Y %I:%M:%S %p')
    return logfile
'''


def init_logging(logger_name, level=logging.DEBUG, log_stdout=False):
    logger = logging.getLogger(logger_name)
    logfile = logger_name+'-'+str(get_current_time())+'.log'
    logs_dir = os.path.join(os.path.curdir, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    logfile = os.path.join(logs_dir, logfile)
    formatter = logging.Formatter('%(asctime)s : %(message)s')
    fileHandler = logging.FileHandler(logfile, mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(fileHandler)
    if log_stdout:
        logger.addHandler(streamHandler)
    return logger_name


def is_none_or_empty(data):
    if data == None or len(data) == 0:
        return True
    else:
        return False


def list_from_path(path='/'):
    if path:
        if path[0] == '/':
            if path[-1] == '/':
                return re.split('''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)[1:-1]
            else:
                return re.split('''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)[1:]
        else:
            if path[-1] == '/':
                return re.split('''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)[:-1]
            else:
                return re.split('''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)
    return []


def path_from_string(path='/'):
    mypath = []

    for e in list_from_path(path):
        eName = e.split("[", 1)[0]
        eKeys = re.findall('\[(.*?)\]', e)
        #print ('eName: %s, eKey: %s' % (eName, eKey))
        dKeys = dict(x.split('=', 1) for x in eKeys)
        mypath.append(gnmi_pb2.PathElem(name=eName, key=dKeys))

    full_path = gnmi_pb2.Path(elem=mypath)
    # dump_object(full_path)
    return full_path


def gnmi_path_to_string(subscription):
    # print_type(subscription)
    path = ''
    name = ''
    for ele in subscription.path.elem:
        path = path + '/' + ele.name
        if ele.key == None or len(ele.key) == 0:
            continue
        for key in ele.key:
            path = path + '[' + key + ':' + ele.key[key] + ']'
            name = ele.key[key]
    return path, name


def get_subscription_type(path):
    if path.find(RequestPathBase.BASE_PORT_PATH) != -1:
        return RequestType.PORT
    if path.find(RequestPathBase.BASE_FLOW_PATH) != -1:
        return RequestType.FLOW
    return RequestType.PROTOCOL


def get_subscription_mode_string(mode):
    if mode == 0:
        return 'STREAM'
    if mode == 1:
        return 'ONCE'
    if mode == 2:
        return 'POLL'
