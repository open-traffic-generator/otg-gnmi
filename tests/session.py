import time
import grpc
from otg_gnmi.autogen import gnmi_pb2, gnmi_pb2_grpc
from tests.utils.settings import GnmiSettings
from otg_gnmi.common.utils import init_logging, path_from_string, is_none_or_empty, get_current_time # noqa
import json

'''
python3 -m tests.session --submode 1 --encoding 2 "/port_metrics[name=P1]" "/flow_metrics[name=F1]" "/bgpv4_metrics[name=BGP Peer 1]" "/flow_metrics[name=F2]"
python3 -m tests.session --server 10.72.47.36:50051 --submode 1 --encoding 2 "/port_metrics[name=P1]" "/flow_metrics[name=F1]" "/bgpv4_metrics[name=BGP Router 1]" "/flow_metrics[name=F2]"

'--submode' --> [TARGET_DEFINED, ON_CHANGE, SAMPLE]
'--mode' --> [STREAM, ONCE, POLL]
'--encoding' --> [JSON, BYTES, PROTO, ASCII, JSON_IETF]
''' # noqa


class Session(object):

    def __init__(self):
        self.logfile = 'gNMIClient'+'-'+str(get_current_time())+'.log'
        self.logger = init_logging(
            'test',
            'Session',
            self.logfile
        )
        self.options = self.init_options()
        self.channel = self.init_channel()
        self.stub = self.init_stub()

    def init_options(self):
        self.logger.debug("Create gNMI options")
        options = GnmiSettings()
        return options

    def is_secure(self):
        if self.options.secure is True and len(self.options.cert) == 0:
            return False
        return True

    def init_channel(self):
        self.logger.info("Create gNMI channel")
        channel = None
        self.logger.info('Options: %s', self.options.to_string())
        if self.options.secure:
            self.logger.info(
                "Create SSL Channel [connection: %s]", self.options.server)
            if self.options.servercrt:
                certificate = None
                # https://github.com/grpc/grpc/issues/6722
                opts = []
                opts.append(('grpc.ssl_target_name_override',
                            self.options.ssl_target_name_override,))
                with open(self.options.servercrt, 'rb') as f:
                    certificate = f.read()
                cred = grpc.ssl_channel_credentials(
                    root_certificates=certificate)
                channel = grpc.secure_channel(self.options.server, cred, opts)
        else:
            self.logger.info("Create insecure Channel")
            channel = grpc.insecure_channel(self.options.server)

        return channel

    def init_stub(self):
        self.logger.debug("Create gNMI stub")
        stub = gnmi_pb2_grpc.gNMIStub(self.channel)
        return stub

    def capabilites(self):

        result = True
        self.logger.info('Sending CapabilityRequest')
        try:
            request = gnmi_pb2.CapabilityRequest()
            responses = self.stub.Capabilities(
                request, metadata=self.options.metadata)
            print("Hi")
            print(responses)
            self.logger.info('CapabilityRequest Response: %s', responses)
            if responses is not None:
                result = True

        except KeyboardInterrupt:
            self.logger.info("Stopped by user")
            result = False

        except grpc.RpcError as x:
            self.logger.error("RPC Error: %s", x.details)
            result = False

        except Exception as err:
            self.logger.error("Exception: s", err)
            result = False

        return result

    def get(self):

        result = True
        self.logger.info('Sending GetRequest')
        try:
            request = gnmi_pb2.GetRequest()
            responses = self.stub.Get(request, metadata=self.options.metadata)
            self.logger.info('GetRequest Response: %s', responses)
            if responses is not None:
                result = True

        except KeyboardInterrupt:
            self.logger.info("Stopped by user")
            result = False

        except grpc.RpcError as x:
            self.logger.error("RPC Error: %s", x.details)
            result = False

        except Exception as err:
            self.logger.error("Exception: s", err)
            result = False

        return result

    def set(self):

        result = True
        self.logger.info('Sending SetRequest')
        try:
            path = gnmi_pb2.Path(elem=[
                gnmi_pb2.PathElem(name='val', key={'name': 'setup_test'})
            ])
            update = gnmi_pb2.Update(path=path, val=gnmi_pb2.TypedValue(
                json_val=json.dumps({'name': 'setup_test'}).encode("utf-8")))
            updates = []
            updates.append(update)
            request = gnmi_pb2.SetRequest(update=updates)
            responses = self.stub.Get(request, metadata=self.options.metadata)
            self.logger.info('SetRequest Response: %s', responses)
            if responses is not None:
                result = True

        except KeyboardInterrupt:
            self.logger.info("Stopped by user")
            result = False

        except grpc.RpcError as x:
            self.logger.error("RPC Error: %s", x.details)
            result = False

        except Exception as err:
            self.logger.error("Exception: s", err)
            result = False

        return result

    def generate_subscription_request(self, subscription_types):
        mysubs = []

        paths = []
        self.logger.info('Create SubscribeRequest: %s - Start',
                         subscription_types)
        for type in subscription_types:
            if type == 'port_metrics':
                paths.extend(self.options.port_metrics)
            if type == 'flow_metrics':
                paths.extend(self.options.flow_metrics)
            if type == 'bgpv4_metrics':
                paths.extend(self.options.bgpv4_metrics)
            if type == 'bgpv6_metrics':
                paths.extend(self.options.bgpv6_metrics)
            if type == 'isis_metrics':
                paths.extend(self.options.isis_metrics)
            if type == 'ipv4_neighbors':
                paths.extend(self.options.ipv4_neighbors)
            if type == 'ipv6_neighbors':
                paths.extend(self.options.ipv6_neighbors)

        for path in paths:
            mypath = path_from_string(path)
            self.logger.info('Sending SubscribeRequest: %s: %s', path, mypath)
            mysub = gnmi_pb2.Subscription(
                path=mypath, mode=self.options.submode,
                suppress_redundant=self.options.suppress,
                sample_interval=self.options.interval*1000000000,
                heartbeat_interval=self.options.heartbeat)
            mysubs.append(mysub)

        if is_none_or_empty(self.options.prefix):
            myprefix = None
        else:
            myprefix = path_from_string(self.options.prefix)

        if is_none_or_empty(self.options.qos):
            myqos = None
        else:
            myqos = gnmi_pb2.QOSMarking(marking=self.options.qos)

        mysblist = gnmi_pb2.SubscriptionList(
            prefix=myprefix,
            mode=self.options.mode,
            allow_aggregation=self.options.aggregate,
            encoding=self.options.encoding,
            subscription=mysubs,
            use_aliases=self.options.use_alias,
            qos=myqos)
        mysubreq = gnmi_pb2.SubscribeRequest(subscribe=mysblist)
        self.logger.info('Create SubscribeRequest: %s - End',
                         subscription_types)

        print(mysubreq)

        yield mysubreq

    def subscribe(self, subscription_types):

        result = True
        req_iterator = self.generate_subscription_request(subscription_types)

        start = 0
        secs = 0
        upd_cnt = 0
        resp_cnt = 0
        try:
            self.logger.info('Sending SubscribeRequest: %s', req_iterator)
            responses = self.stub.Subscribe(
                req_iterator, None, metadata=self.options.metadata)
            res_idx = 0
            for response in responses:

                self.logger.info('Response[%s]: %s', res_idx, response)
                res_idx = res_idx + 1

                if response.HasField('error'):
                    self.logger.error('gNMI Error Code %s, Error Message: %s',
                                      str(response.error.code),
                                      str(response.error.message))

                elif response.HasField('sync_response'):
                    self.logger.info('Sync Response received\n'+str(response))
                    secs += time.time() - start
                    start = 0
                    if self.options.stats:
                        self.logger.info(
                            "Total Messages: %d [Rate: %5.0f], Total Updates: %d [Rate: %5.0f], Total Time: %1.2f secs", # noqa
                            resp_cnt,
                            resp_cnt/secs,
                            upd_cnt,
                            upd_cnt/secs,
                            secs)

                elif response.HasField('update'):
                    if start == 0:
                        start = time.time()
                    resp_cnt += 1
                    upd_cnt += len(response.update.update)
                    if not self.options.stats:
                        self.logger.info('Update received\n'+str(response))
                else:
                    self.logger.error(
                        'Received unknown response: %s', str(response))

                if self.options.is_done(upd_cnt, len(subscription_types)*2):
                    self.logger.info('Completed, exiting now.\n')
                    break

        except KeyboardInterrupt:
            self.logger.info("Stopped by user")
            result = False

        except grpc.RpcError as x:
            self.logger.error("RPC Error: %s", x.details)
            result = False

        except Exception as err:
            self.logger.error("Excepion: s", err)
            result = False

        return result


if __name__ == '__main__':
    sessoin = Session()
    sessoin.subscribe('port_metrics')
    sessoin.subscribe('flow_metrics')
    sessoin.subscribe('bgpv4_metrics')
    sessoin.subscribe('bgpv6_metrics')
    sessoin.subscribe('isis_metrics')
    sessoin.subscribe('ipv4_neighbors')
    sessoin.subscribe('ipv6_neighbors')
