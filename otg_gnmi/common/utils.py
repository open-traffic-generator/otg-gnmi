import datetime
import logging
import os
import re
from enum import Enum

from ..autogen import gnmi_pb2


class CustomFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        arg_pattern = re.compile(r'%\((\w+)\)')
        arg_names = [x.group(1) for x in arg_pattern.finditer(self._fmt)]
        for field in arg_names:
            if field not in record.__dict__:
                record.__dict__[field] = None

        return super().format(record)


class RequestPathBase():
    BASE_PORT_PATH = r'/port_metrics'
    BASE_FLOW_PATH = r'/flow_metrics'
    BASE_BGPv4_PATH = r'/bgpv4_metrics'
    BASE_BGPv6_PATH = r'/bgpv6_metrics'
    BASE_ISIS_PATH = r'/isis_metrics'


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


def init_logging(ctx, scope, logfile, level=logging.DEBUG, log_stdout=False):
    logger_name = ctx + '_' + scope
    logger = logging.getLogger(logger_name)
    logs_dir = os.path.join(os.path.curdir, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    logfile = os.path.join(logs_dir, logfile)
    if ctx in ['profile']:
        log_format = "{'level': '%(levelname)s',\
            'ctx': '" + ctx + "',\
            'api': '%(funcName)s',\
            'scope': '" + scope + "', \
            'nanoseconds': '%(nanoseconds)s',\
            'ts':'%(asctime)s.%(msecs)03dZ',\
            'msg': '%(message)s'}"
    else:
        log_format = "{'level': '%(levelname)s',\
            'ctx': '" + ctx + "',\
            'scope': '" + scope + "', \
            'api': '%(funcName)s',\
            'ts':'%(asctime)s.%(msecs)03dZ',\
            'msg': '%(message)s'}"
    formatter = CustomFormatter(log_format, "%Y-%m-%dT%H:%M:%S")
    fileHandler = logging.FileHandler(logfile, mode='a')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(fileHandler)
    if log_stdout:
        logger.addHandler(streamHandler)
    return logger


def is_none_or_empty(data):
    if data is None or len(data) == 0:
        return True
    else:
        return False


def list_from_path(path='/'):
    if path:
        if path[0] == '/':
            if path[-1] == '/':
                return re.split(
                    '''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)[1:-1] # noqa
            else:
                return re.split(
                    '''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)[1:] # noqa
        else:
            if path[-1] == '/':
                return re.split(
                    '''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)[:-1] # noqa
            else:
                return re.split(
                    '''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path) # noqa
    return []


def path_from_string(path='/'):
    mypath = []

    for e in list_from_path(path):
        eName = e.split("[", 1)[0]
        eKeys = re.findall('\[(.*?)\]', e) # noqa
        # print ('eName: %s, eKey: %s' % (eName, eKey))
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
        if ele.key is None or len(ele.key) == 0:
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


def get_time_elapsed(start):
    end = datetime.datetime.now()
    elapsed = end - start
    return elapsed.total_seconds() * 10 ** 9
