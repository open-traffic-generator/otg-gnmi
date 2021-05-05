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
    BASE_PROTOCOL_PATH = r'/bgpv4_metrics'

class RequestType(Enum):
    UNKNOWN = 0
    PORT = 1
    FLOW = 2
    PROTOCOL = 3

def get_current_time():
    current_utc = datetime.datetime.utcnow()
    current_utc = str(current_utc).split('.')[0]
    current_utc = current_utc.replace(' ','-')
    current_utc = current_utc.replace(':','-')
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

def init_logging(logger_name, level=logging.DEBUG):
    l = logging.getLogger(logger_name)
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
    l.setLevel(level)
    l.addHandler(fileHandler)
    #l.addHandler(streamHandler)  
    return logger_name 

def is_none_or_empty(data):
    if data == None or len(data) == 0:
        return True
    else:
        return False

def list_from_path(path='/'):
    if path:
        if path[0]=='/':
            if path[-1]=='/':
                return re.split('''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)[1:-1]
            else:
                return re.split('''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)[1:]
        else:
            if path[-1]=='/':
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
    #dump_object(full_path)
    return full_path

def generate_subscription_request(options):
    mysubs = []
    for path in options.paths:
        mypath = path_from_string(path)
        mysub = gnmi_pb2.Subscription(path=mypath, mode=options.submode, suppress_redundant=options.suppress, sample_interval=options.interval*1000000000, heartbeat_interval=options.heartbeat)
        mysubs.append(mysub)

    if is_none_or_empty(options.prefix):
        myprefix = None
    else:
        myprefix = path_from_string(options.prefix)			

    if is_none_or_empty(options.qos):
        myqos = None
    else:
        myqos = gnmi_pb2.QOSMarking(marking=options.qos)
    
    mysblist = gnmi_pb2.SubscriptionList(prefix=myprefix, mode=options.mode, allow_aggregation=options.aggregate, encoding=options.encoding, subscription=mysubs, use_aliases=options.use_alias, qos=myqos)
    mysubreq = gnmi_pb2.SubscribeRequest( subscribe=mysblist )

    yield mysubreq


async def gnmi_path_generator(path_in_question):
    gnmi_path = Path()

    path_elements = path_in_question.split('/')
    print(path_elements)

    for pe_entry in path_elements:
        if not re.match('.+?:.+?', pe_entry) and len(path_elements) == 1:
            sys.exit(f'You haven\'t specified either YANG module or the top-level container in \'{pe_entry}\'.')

        elif re.match('.+?:.+?', pe_entry):
            gnmi_path.origin = pe_entry.split(':')[0]
            gnmi_path.elem.add(name=pe_entry.split(':')[1])

        elif re.match('.+?\[.+?\]', pe_entry):
            gnmi_path.elem.add(name=pe_entry.split('[')[0], key={f'{pe_entry.split("[")[1].split("=")[0]}': f'{re.sub("]", "", pe_entry.split("[")[1].split("=")[1])}'})

        else:
            gnmi_path.elem.add(name=pe_entry)

    return gnmi_path

    
def gnmi_path_to_string(subscription):
    #print_type(subscription)    
    path = ''
    name = ''
    for ele in subscription.path.elem:
        path = path + '/' + ele.name
        if ele.key == None or len(ele.key) == 0:
            continue
        for key in ele.key:
            path = path +  '[' + key + ':' + ele.key[key] + ']'        
            name = ele.key[key]
    return path, name

def get_subscription_type(path):
    if path.find(RequestPathBase.BASE_PORT_PATH) != -1:
        return RequestType.PORT
    if path.find(RequestPathBase.BASE_FLOW_PATH) != -1:
        return RequestType.FLOW
    if path.find(RequestPathBase.BASE_PROTOCOL_PATH) != -1:
        return RequestType.PROTOCOL
    return RequestType.UNKNOWN

def get_subscription_mode_string(mode):
    if mode == 0:
        return 'STREAM'
    if mode == 1:
        return 'ONCE'
    if mode == 2:
        return 'POLL'