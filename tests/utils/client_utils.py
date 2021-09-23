import re

from otg_gnmi.autogen import gnmi_pb2


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
                    '''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)[1:-1]  # noqa
            else:
                return re.split(
                    '''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)[1:]  # noqa
        else:
            if path[-1] == '/':
                return re.split(
                    '''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)[:-1]  # noqa
            else:
                return re.split(
                    '''/(?=(?:[^\[\]]|\[[^\[\]]+\])*$)''', path)  # noqa
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


def generate_subscription_request(options):
    mysubs = []
    for path in options.paths:
        mypath = path_from_string(path)
        mysub = gnmi_pb2.Subscription(
            path=mypath,
            mode=options.submode,
            suppress_redundant=options.suppress,
            sample_interval=options.interval*1000000000,
            heartbeat_interval=options.heartbeat)
        mysubs.append(mysub)

    if is_none_or_empty(options.prefix):
        myprefix = None
    else:
        myprefix = path_from_string(options.prefix)

    if is_none_or_empty(options.qos):
        myqos = None
    else:
        myqos = gnmi_pb2.QOSMarking(marking=options.qos)

    mysblist = gnmi_pb2.SubscriptionList(
        prefix=myprefix,
        mode=options.mode,
        allow_aggregation=options.aggregate,
        encoding=options.encoding,
        subscription=mysubs,
        use_aliases=options.use_alias,
        qos=myqos)
    mysubreq = gnmi_pb2.SubscribeRequest(
        subscribe=mysblist)

    yield mysubreq
