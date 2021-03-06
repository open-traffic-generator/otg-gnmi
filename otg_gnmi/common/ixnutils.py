# ixnutils.py
import asyncio
import datetime
import json
import time
import types
from threading import Lock, Thread
import logging

import snappi
from google.protobuf.any_pb2 import Any

from ..autogen import gnmi_pb2

from snappi import otg_pb2
from .client_session import ClientSession
from .utils import (RequestPathBase, RequestType, get_subscription_type,
                    get_time_elapsed, gnmi_path_to_string, init_logging)

ATHENA_POLL_INTERVAL = 0.05
IXN_POLL_INTERVAL = 4
POLL_INTERVAL = IXN_POLL_INTERVAL

g_RequestId = -1


def get_request_id():
    global g_RequestId
    g_RequestId += 1


class SubscriptionReq:
    def __init__(self, subscriptionList, session, subscription):
        # Assign subscriptionList properties
        self.client = session
        self.parent_encoding = subscriptionList.encoding
        self.parent_mode = subscriptionList.mode

        # Assign subscription item peroperties
        self.uniqueId = get_request_id()
        self.mode = subscription.mode
        self.gnmipath = subscription.path
        self.stringpath, self.name, self.key = gnmi_path_to_string(
            subscription
        )
        self.type = get_subscription_type(self.stringpath)
        self.callback, self.deserializer = TestManager.Instance().get_callback(
            self.stringpath
        )
        self.sample_interval = subscription.sample_interval
        self.last_polled = None
        self.last_yield = None
        self.active = False
        self.curr_stats = None
        self.prev_stats = None
        self.delta_stats = None
        self.encoded_stats = None
        self.availabel_cols = []
        self.subscribed_cols = []
        self.error = None

    def encode_stats(self, stats_name):

        def add_header(stats_name, val):
            path = gnmi_pb2.Path(elem=[
                gnmi_pb2.PathElem(name='val', key={'name': stats_name})
            ])
            update = gnmi_pb2.Update(path=path, val=val)
            milliseconds = int(round(time.time() * 1000))
            notification = gnmi_pb2.Notification(
                timestamp=milliseconds, update=[update])
            sub_res = gnmi_pb2.SubscribeResponse(update=notification)
            return sub_res

        stats = None
        if self.mode == gnmi_pb2.SubscriptionMode.ON_CHANGE:

            if self.delta_stats is None or len(self.delta_stats) == 0:
                self.encoded_stats = None
                return
            stats = json.dumps(self.delta_stats)
        else:
            stats = self.curr_stats.serialize()

        val = None
        if (self.parent_encoding == gnmi_pb2.Encoding.JSON):
            val = gnmi_pb2.TypedValue(json_val=stats.encode("utf-8"))
            self.encoded_stats = add_header(stats_name, val)
            return
        if (self.parent_encoding == gnmi_pb2.Encoding.JSON_IETF):
            val = gnmi_pb2.TypedValue(json_ietf_val=stats.encode("utf-8"))
            self.encoded_stats = add_header(stats_name, val)
            return
        if (self.parent_encoding == gnmi_pb2.Encoding.PROTO):
            stats = self.encode_metrics(stats)
            val = stats
            val = gnmi_pb2.TypedValue(any_val=stats)
            self.encoded_stats = add_header(stats_name, val)
            return

    def encode_metrics(self, stats_json):
        stats = json.loads(stats_json)
        metric = self.deserializer.deserialize(stats)
        target = Any()
        target.Pack(metric)
        return target

    def compute_delta(self):
        delta = {}
        if self.curr_stats is None:
            self.delta_stats = None
            return

        if self.prev_stats is None:
            for key, curr_value in self.curr_stats._properties.items():
                delta[key] = curr_value
            self.delta_stats = delta
            return

        for key, curr_value in self.curr_stats._properties.items():
            prev_val = self.prev_stats._get_property(key)
            if curr_value != prev_val:
                delta[key] = curr_value
        self.delta_stats = delta
        return


class TestManager:
    m_instance = None

    def __init__(self):
        """ Constructor.
        """
        if TestManager.m_instance is None:
            TestManager.m_instance = self
            self.init_once = False
        else:
            raise Exception("You cannot create another TaskScheduler class")

    @staticmethod
    def Instance():
        """ Static method to fetch the current instance.
        """
        if not TestManager.m_instance:
            TestManager()
        return TestManager.m_instance

    async def init_once_func(self, options):
        api_start = datetime.datetime.now()
        try:
            try:
                if self.init_once is False:
                    self.app_mode = options.app_mode
                    self.unittest = options.unittest
                    self.target_address = options.target_address
                    log_stdout = not options.no_stdout

                    self.logger = init_logging(
                        'gnmi',
                        'ixutils-TestManager',
                        options.logfile,
                        logging.DEBUG,
                        log_stdout
                    )

                    self.profile_logger = init_logging(
                        'profile',
                        'ixutils-TestManager',
                        options.logfile,
                        logging.DEBUG,
                        log_stdout
                    )

                    self.api = None
                    self.stopped = False

                    self.client_sessions = {}
                    self.port_subscriptions = {}
                    self.flow_subscriptions = {}
                    self.neighbor_subscriptions = {}
                    self.protocol_subscriptions = {}

                    self.lock = Lock()
                    self.get_api()
                    self.start_worker_threads()

                    self.init_once = True
                    return self.init_once, None
            except Exception as ex:
                return self.init_once, str(ex)
            return self.init_once, None
        finally:
            self.profile_logger.info(
                "init_once_func completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    async def get_supported_models(self):
        api_start = datetime.datetime.now()
        try:
            def get_supported_models():
                supported_models = []
                otg_model = gnmi_pb2.ModelData(
                    name='open-traffic-generator',
                    organization='otg',
                    version=get_version()
                )
                supported_models.append(otg_model)
                return supported_models

            def get_supported_encodings():
                supported_encodings = []
                supported_encodings.append(gnmi_pb2.Encoding.JSON)
                supported_encodings.append(gnmi_pb2.Encoding.JSON_IETF)
                supported_encodings.append(gnmi_pb2.Encoding.PROTO)
                return supported_encodings

            def get_version():
                return '0.0.1'

            cap_response = gnmi_pb2.CapabilityResponse(
                supported_models=get_supported_models(),
                supported_encodings=get_supported_encodings(),
                gNMI_version=get_version()
            )
            return cap_response
        finally:
            if hasattr(self, 'profile_logger'):
                self.profile_logger.info(
                    "get_supported_models completed!", extra={
                        'nanoseconds':  get_time_elapsed(api_start)
                    }
                )

    def start_worker_threads(self):
        api_start = datetime.datetime.now()
        try:
            self.logger.info('Starting all collection threads')
            self.flow_stats_thread = Thread(
                target=self.collect_flow_stats, args=[])
            self.flow_stats_thread.start()
            self.neighbor_stats_thread = Thread(
                target=self.collect_neighbor_states, args=[])
            self.neighbor_stats_thread.start()
            self.port_stats_thread = Thread(
                target=self.collect_port_stats, args=[])
            self.port_stats_thread.start()
            self.protocol_stats_thread = Thread(
                target=self.collect_protocol_stats, args=[])
            self.protocol_stats_thread.start()
        finally:
            self.profile_logger.info(
                "start_worker_threads completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def stop_worker_threads(self):
        api_start = datetime.datetime.now()
        try:
            if hasattr(self, 'logger'):
                self.logger.info('Stopping all collection threads')
            self.stopped = True
            if hasattr(self, 'flow_stats_thread'):
                self.flow_stats_thread.join()
            if hasattr(self, 'neighbor_stats_thread'):
                self.neighbor_stats_thread.join()
            if hasattr(self, 'port_stats_thread'):
                self.port_stats_thread.join()
            if hasattr(self, 'protocol_stats_thread'):
                self.protocol_stats_thread.join()
        finally:
            if hasattr(self, 'profile_logger'):
                self.profile_logger.info(
                    "stop_worker_threads completed!", extra={
                        'nanoseconds':  get_time_elapsed(api_start)
                    }
                )

    async def terminate(self, request_iterator):
        api_start = datetime.datetime.now()
        try:
            self.logger.info('Terminate connection')
            self.stop_worker_threads()
            await self.deregister_subscription(request_iterator)
            self.dump_all_subscription()
        finally:
            self.profile_logger.info(
                "terminate completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    async def create_session(self, context, request_iterator):
        api_start = datetime.datetime.now()
        try:
            self.lock.acquire()
            session = None
            if context in self.client_sessions:
                session = self.client_sessions[context]
            else:
                requests = []
                await asyncio.wait_for(
                        self.parse_requests(request_iterator, requests),
                        timeout=1.0
                    )

                session = ClientSession(context, requests)
                self.client_sessions[context] = session
                self.logger.info('Created new session %s', context)
            self.lock.release()
            return session
        finally:
            self.profile_logger.info(
                "create_session completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    async def remove_session(self, context):
        api_start = datetime.datetime.now()
        try:
            self.lock.acquire()
            if context in self.client_sessions:
                session = self.client_sessions.pop(context)
                self.logger.info('Removed new session %s', context)
            self.lock.release()
            return session
        finally:
            self.profile_logger.info(
                "remove_session completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    async def parse_requests(self, request_iterator, requests):
        api_start = datetime.datetime.now()
        try:
            if isinstance(request_iterator, types.GeneratorType):
                for request in request_iterator:
                    requests.append(request)
            else:
                requests.append(await request_iterator.__anext__())
        except Exception as ex:
            self.logger.error('Exception: %s', str(ex))
            self.logger.error('Exception: ', exc_info=True)
        finally:
            self.profile_logger.info(
                "parse_requests completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def get_callback(self, path):
        api_start = datetime.datetime.now()
        try:
            if path.find(RequestPathBase.BASE_PORT_PATH) != -1:
                return self.get_port_metric, otg_pb2.PortMetric()
            if path.find(RequestPathBase.BASE_FLOW_PATH) != -1:
                return self.get_flow_metric, otg_pb2.FlowMetric()
            if path.find(RequestPathBase.BASE_NEIGHBORv4_PATH) != -1:
                return self.get_ipv4_neighbor_state, otg_pb2.Neighborsv4State()
            if path.find(RequestPathBase.BASE_NEIGHBORv6_PATH) != -1:
                return self.get_ipv6_neighbor_state, otg_pb2.Neighborsv6State()
            if path.find(RequestPathBase.BASE_BGPv4_PATH) != -1:
                return self.get_bgpv4_metric, otg_pb2.Bgpv4Metric()
            if path.find(RequestPathBase.BASE_BGPv6_PATH) != -1:
                return self.get_bgpv6_metric, otg_pb2.Bgpv6Metric()
            if path.find(RequestPathBase.BASE_ISIS_PATH) != -1:
                return self.get_isis_metric, otg_pb2.IsisMetric()
            return None
        finally:
            self.profile_logger.info(
                "get_callback completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def collect_stats(self, subscriptions, meta):
        api_start = datetime.datetime.now()
        try:
            self.lock.acquire()
            self._collect_stats(subscriptions, meta)
            self.lock.release()
        finally:
            self.profile_logger.info(
                "collect_stats completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def _collect_stats(self, subscriptions, meta):
        api_start = datetime.datetime.now()
        try:
            if len(subscriptions) == 0:
                return
            names = []
            name_to_sub_reverse_map = {}
            for key in subscriptions:
                sub = subscriptions[key]
                sub.error = None
                names.append(sub.name)
                name_to_sub_reverse_map[sub.name] = sub
            # self.logger.info('Collect %s stats for %s', meta, names)
            try:
                metrics = sub.callback(names)
                # self.logger.info('Collected %s stats for %s', meta, metrics)
                for metric in metrics:
                    key = getattr(metric, sub.key)
                    if key not in name_to_sub_reverse_map:
                        continue
                    sub = name_to_sub_reverse_map[key]
                    sub.prev_stats = sub.curr_stats
                    sub.curr_stats = metric
                    sub.compute_delta()
                    sub.encode_stats(key)

            except Exception as ex:
                for key in subscriptions:
                    sub.error = str(ex)

        except Exception:
            self.logger.error(
                "Fatal error in collecting stats for %s: names:%s",
                meta,
                names
            )
            self.logger.error("Fatal error: ", exc_info=True)
        finally:
            self.profile_logger.info(
                "_collect_stats completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def collect_flow_stats(self):
        api_start = datetime.datetime.now()
        try:
            global POLL_INTERVAL
            self.logger.info('Started flow stats collection thread')
            while self.stopped is False:
                if len(self.flow_subscriptions) > 0:
                    self.collect_stats(self.flow_subscriptions, 'Flow')
                time.sleep(POLL_INTERVAL)
        finally:
            self.profile_logger.info(
                "collect_flow_stats completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def collect_neighbor_states(self):
        api_start = datetime.datetime.now()
        try:
            global POLL_INTERVAL
            self.logger.info('Started neighbor states collection thread')
            while self.stopped is False:
                if len(self.neighbor_subscriptions) > 0:
                    self.collect_stats(self.neighbor_subscriptions, 'Neighbor')
                time.sleep(POLL_INTERVAL)
        finally:
            self.profile_logger.info(
                "collect_neighbor_states completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def collect_port_stats(self):
        api_start = datetime.datetime.now()
        try:
            global POLL_INTERVAL
            self.logger.info('Started port stats collection thread')
            while self.stopped is False:
                if len(self.port_subscriptions) > 0:
                    self.collect_stats(self.port_subscriptions, 'Port')
                time.sleep(POLL_INTERVAL)
        finally:
            self.profile_logger.info(
                "collect_port_stats completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def collect_protocol_stats(self):
        api_start = datetime.datetime.now()
        try:
            global POLL_INTERVAL
            time.sleep(POLL_INTERVAL)
            self.logger.info('Started protocol stats collection thread')
            while self.stopped is False:
                if len(self.protocol_subscriptions) > 0:
                    self.collect_stats(self.protocol_subscriptions, 'Protocol')
                time.sleep(POLL_INTERVAL)
        finally:
            self.profile_logger.info(
                "collect_protocol_stats completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def get_api(self):
        api_start = datetime.datetime.now()
        try:
            if self.init_once:
                return self.api
            target = None
            if self.unittest:
                target = "http://{}".format('127.0.0.1:11020')
            else:
                target = "https://{}".format(self.target_address)
            self.logger.info(
                'Initializing snappi for %s at target %s',
                self.app_mode,
                target
            )
            # when using ixnetwork extension, host is IxNetwork API Server

            if self.app_mode == 'ixnetwork':
                self.api = snappi.api(location=target, ext='ixnetwork')
            else:
                global POLL_INTERVAL
                POLL_INTERVAL = ATHENA_POLL_INTERVAL
                self.api = snappi.api(location=target)
            self.logger.info('Initialized snappi...')
            return self.api
        finally:
            self.profile_logger.info(
                "get_api completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def get_flow_metric(self, flow_names, stat_names=None):
        api_start = datetime.datetime.now()
        try:
            api = self.get_api()
            req = api.metrics_request()
            req.choice = "flow"
            req.flow.flow_names = flow_names
            res = api.get_metrics(req)
            return res.flow_metrics
        finally:
            self.profile_logger.info(
                "get_flow_metric completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def get_port_metric(self, port_names, stat_names=None):
        api_start = datetime.datetime.now()
        try:
            api = self.get_api()
            req = api.metrics_request()
            req.choice = "port"
            req.port.port_names = port_names
            res = api.get_metrics(req)
            return res.port_metrics
        finally:
            self.profile_logger.info(
                "get_port_metric completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def get_bgpv6_metric(self, peer_names, stat_names=None):
        api_start = datetime.datetime.now()
        try:
            api = self.get_api()
            req = api.metrics_request()
            req.choice = "bgpv6"
            req.bgpv6.peer_names = peer_names
            res = api.get_metrics(req)
            return res.bgpv6_metrics
        finally:
            self.profile_logger.info(
                "get_bgpv6_metric completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def get_bgpv4_metric(self, peer_names, stat_names=None):
        api_start = datetime.datetime.now()
        try:
            api = self.get_api()
            req = api.metrics_request()
            req.choice = "bgpv4"
            req.bgpv4.peer_names = peer_names
            res = api.get_metrics(req)
            return res.bgpv4_metrics
        finally:
            self.profile_logger.info(
                "get_bgpv4_metric completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def get_isis_metric(self, router_names, stat_names=None):
        api_start = datetime.datetime.now()
        try:
            api = self.get_api()
            req = api.metrics_request()
            req.choice = "isis"
            req.isis.router_names = router_names
            res = api.get_metrics(req)
            return res.isis_metrics
        finally:
            self.profile_logger.info(
                "get_isis_metric completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def get_ipv4_neighbor_state(self, eth_names, stat_names=None):
        api_start = datetime.datetime.now()
        try:
            api = self.get_api()
            req = api.states_request()
            req.choice = "ipv4_neighbors"
            req.ipv4_neighbors.ethernet_names = eth_names
            res = api.get_states(req)
            return res.ipv4_neighbors
        finally:
            self.profile_logger.info(
                "get_ipv4_neighbor_state completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def get_ipv6_neighbor_state(self, eth_names, stat_names=None):
        api_start = datetime.datetime.now()
        try:
            api = self.get_api()
            req = api.states_request()
            req.choice = "ipv6_neighbors"
            req.ipv6_neighbors.ethernet_names = eth_names
            res = api.get_states(req)
            return res.ipv6_neighbors
        finally:
            self.profile_logger.info(
                "get_ipv6_neighbor_state completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def create_update_response(self, encoding, stats_name, stats):
        api_start = datetime.datetime.now()
        try:
            val = None
            if encoding == gnmi_pb2.Encoding.JSON:
                val = gnmi_pb2.TypedValue(json_val=stats.encode("utf-8"))
            if encoding == gnmi_pb2.Encoding.JSON_IETF:
                val = gnmi_pb2.TypedValue(json_ietf_val=stats.encode("utf-8"))
            if encoding == gnmi_pb2.Encoding.PROTO:
                val = gnmi_pb2.TypedValue(any_val=stats)

            path = gnmi_pb2.Path(elem=[
                gnmi_pb2.PathElem(name='val', key={'name': stats_name})
            ])
            update = gnmi_pb2.Update(path=path, val=val)
            milliseconds = int(round(time.time() * 1000))
            notification = gnmi_pb2.Notification(
                timestamp=milliseconds, update=[update])
            sub_res = gnmi_pb2.SubscribeResponse(update=notification)
            return sub_res
        finally:
            self.profile_logger.info(
                "create_update_response completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def encode_sync(self):
        api_start = datetime.datetime.now()
        try:
            sync_resp = gnmi_pb2.SubscribeResponse(sync_response=True)
            return sync_resp
        finally:
            self.profile_logger.info(
                "encode_sync completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def create_error_response(self, stats_name, error_message):
        api_start = datetime.datetime.now()
        try:
            # err = gnmi_pb2.Error(data=stats_name, message=error_message)
            err = gnmi_pb2.Error(message=stats_name + ': ' + error_message)
            err_res = gnmi_pb2.SubscribeResponse(error=err)
            return err_res
        finally:
            self.profile_logger.info(
                "create_error_response completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    def dump_all_subscription(self):
        api_start = datetime.datetime.now()
        try:
            self.logger.info(
                'Port Subscriptions: total subscription = %s', len(
                    self.port_subscriptions))
            for path in self.port_subscriptions:
                sub = self.port_subscriptions[path]
                self.logger.info(
                    '\t\tSubscriptions: %s, [Key: %s, Name: %s]',
                    path,
                    sub.key,
                    sub.name
                )

            self.logger.info(
                'Flow Subscriptions: total subscription = %s', len(
                    self.flow_subscriptions)
                )
            for path in self.flow_subscriptions:
                sub = self.flow_subscriptions[path]
                self.logger.info(
                    '\t\tSubscriptions: %s, [Key: %s, Name: %s]',
                    path,
                    sub.key,
                    sub.name
                )

            self.logger.info(
                'Neighbor Subscriptions: total subscription = %s', len(
                    self.neighbor_subscriptions))
            for path in self.neighbor_subscriptions:
                sub = self.neighbor_subscriptions[path]
                self.logger.info(
                    '\t\tSubscriptions: %s, [Key: %s, Name: %s]',
                    path,
                    sub.key,
                    sub.name
                )

            self.logger.info(
                'Protocol Subscriptions: total subscription = %s',
                len(self.protocol_subscriptions)
            )
            for path in self.protocol_subscriptions:
                sub = self.protocol_subscriptions[path]
                self.logger.info(
                    '\t\tSubscriptions: %s, [Key: %s, Name: %s]',
                    path,
                    sub.key,
                    sub.name
                )
        finally:
            self.profile_logger.info(
                "dump_all_subscription completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    async def register_subscription(self, session):
        api_start = datetime.datetime.now()
        try:
            self.lock.acquire()
            self.logger.info(
                'Register Subscription for %s elements', len(session.requests))
            try:
                for request in session.requests:
                    if request is None:
                        continue
                    session.mode = request.subscribe.mode
                    for subscription in request.subscribe.subscription:
                        sub = SubscriptionReq(
                            request.subscribe, session, subscription)
                        sub.client.register_path(sub.stringpath)
                        sub.encoding = request.subscribe.encoding
                        self.logger.info(
                            'Register Subscription %s', sub.stringpath)
                        if sub.type == RequestType.PORT:
                            self.port_subscriptions[sub.stringpath] = sub
                        elif sub.type == RequestType.FLOW:
                            self.flow_subscriptions[sub.stringpath] = sub
                        elif sub.type == RequestType.NEIGHBOR:
                            self.neighbor_subscriptions[sub.stringpath] = sub
                        elif sub.type == RequestType.PROTOCOL:
                            self.protocol_subscriptions[sub.stringpath] = sub
                        else:
                            self.logger.info(
                                'Unknown Subscription %s', sub.stringpath)
            except Exception as ex:
                self.logger.error('Exception: %s', str(ex))
                self.logger.error('Exception: ', exc_info=True)

            self.dump_all_subscription()
            self.lock.release()
        finally:
            self.profile_logger.info(
                "register_subscription completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    async def deregister_subscription(self, session):
        api_start = datetime.datetime.now()
        try:
            self.lock.acquire()

            self.logger.info(
                'Deregister Subscription for %s elements', len(
                    session.requests))
            try:
                for request in session.requests:
                    if request is None:
                        continue
                    session.mode = request.subscribe.mode
                    for subscription in request.subscribe.subscription:
                        sub = SubscriptionReq(
                            request.subscribe, session, subscription)
                        sub.client.deregister_path(sub.stringpath)
                        self.logger.info(
                            'Deregister Subscription %s', sub.stringpath)
                        if sub.type == RequestType.PORT:
                            self.port_subscriptions.pop(sub.stringpath)
                        elif sub.type == RequestType.FLOW:
                            self.flow_subscriptions.pop(sub.stringpath)
                        elif sub.type == RequestType.NEIGHBOR:
                            self.neighbor_subscriptions.pop(sub.stringpath)
                        elif sub.type == RequestType.PROTOCOL:
                            self.protocol_subscriptions.pop(sub.stringpath)
            except Exception as ex:
                self.logger.error('Exception: %s', str(ex))
                self.logger.error('Exception: ', exc_info=True)

            self.dump_all_subscription()
            self.lock.release()
            # self.stop_worker_threads()

        finally:
            self.profile_logger.info(
                "deregister_subscription completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    async def publish_stats(self, session):
        api_start = datetime.datetime.now()
        try:
            results = []

            def publish(key, subscriptions, session, res, meta=None):
                # self.logger.info('Publish %s Stats %s', meta, key)
                sub = subscriptions[key]

                if sub.error is not None:
                    res.append(self.create_error_response(
                        sub.name, sub.error))
                    return

                if sub.encoded_stats is not None:
                    res.append(sub.encoded_stats)
                    sub.client.update_stats(key)

            self.lock.acquire()
            for key in self.port_subscriptions:
                publish(key, self.port_subscriptions, session, results, 'Port')

            for key in self.flow_subscriptions:
                publish(key, self.flow_subscriptions, session, results, 'Flow')

            for key in self.neighbor_subscriptions:
                publish(
                    key,
                    self.neighbor_subscriptions,
                    session,
                    results,
                    'Neighbor'
                )

            for key in self.protocol_subscriptions:
                publish(key, self.protocol_subscriptions,
                        session, results, 'Protocol')
            self.lock.release()

            if session.send_sync():
                results.append(self.encode_sync())

            return results

        finally:
            self.profile_logger.info(
                "publish_stats completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )

    async def keep_polling(self):
        api_start = datetime.datetime.now()
        try:
            return self.stopped is False
        finally:
            self.profile_logger.info(
                "keep_polling completed!", extra={
                    'nanoseconds':  get_time_elapsed(api_start)
                }
            )


# if __name__ == 'main':
# setup_test()
