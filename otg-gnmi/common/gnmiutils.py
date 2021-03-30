import logging
import json
import asyncio 
import time
from enum import Enum

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

def dump_object(obj):
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))

def print_type(obj, dump=False):
    print ('Path Type: %s' % (type(obj)))
    if dump:
        dump_object(obj)

def log_type_and_value(name, obj):    
    print("%s type = %s" % (name, type(obj)))
    print("%s val = %s" % (name, obj))

def log_subscribtion_details(request):
    log_type_and_value('request', request) 
    log_type_and_value('request.subscribe', request.subscribe) 
    log_type_and_value('request.subscribe.subscription', request.subscribe.subscription) 
    index = 0
    for subs in request.subscribe.subscription:
        tag = 'request.subscribe.subscription['+str(index)+']\n'
        log_type_and_value(tag, subs)
        index = index + 1



