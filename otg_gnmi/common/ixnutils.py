# utils.pyfrom __future__ import print_function
import logging
import json
import asyncio 
import time
from threading import Thread, Lock
import traceback


from google.protobuf.any_pb2 import Any
from google.protobuf.json_format import Parse

import snappi

from ..autogen import gnmi_pb2_grpc, gnmi_pb2
from ..autogen import otg_pb2
from .utils import *

class TimeIt(object):
    def __call__(self, f):
        @functools.wraps(f)
        def decorated(*args, **kwds):
            with self:
                print ('Executing: %s(%s)' % (f, args))
                return f(*args, **kwds)
        return decorated

    def __enter__(self):
        self.start_time = time.time()

    def __exit__(self, *args, **kw):
        elapsed = time.time() - self.start_time
        print("{:.3} sec".format(elapsed))


g_RequestId = -1
def get_request_id():
    global g_RequestId
    g_RequestId += 1    


class SubscriptionReq:
    def __init__(self, subscriptionList, subscription):
        # Assign subscriptionList properties
        self.parent_encoding = subscriptionList.encoding
        self.parent_mode = subscriptionList.mode
        
        # Assign subscription item peroperties
        self.uniqueId = get_request_id()
        self.mode = subscription.mode        
        self.gnmipath = subscription.path
        self.stringpath, self.name = gnmi_path_to_string(subscription)
        self.type = get_subscription_type(self.stringpath)
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
        self.client = []
        self.error = None
        


    def encode_stats(self, stats_name): 
        
        def add_header(stats_name, val):   
            path = gnmi_pb2.Path(elem=[                
                gnmi_pb2.PathElem(name='val', key={'name': stats_name})
            ])
            update = gnmi_pb2.Update(path=path, val=val)    
            milliseconds = int(round(time.time() * 1000))
            notification = gnmi_pb2.Notification(timestamp=milliseconds, update=[update])
            sub_res = gnmi_pb2.SubscribeResponse(update=notification)
            return sub_res
            
        stats = None
        if self.mode == gnmi_pb2.SubscriptionMode.ON_CHANGE:

            if self.delta_stats == None or len(self.delta_stats) == 0:
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
            if  self.type == RequestType.PORT:
                stats = self.encode_port_metric(stats)
            if  self.type == RequestType.FLOW:
                stats = self.encode_flow_metric(stats)
            if  self.type == RequestType.PROTOCOL:
                stats = self.encode_protocol_metric(stats)
            val = stats
            val = gnmi_pb2.TypedValue(any_val=stats)
            self.encoded_stats = add_header(stats_name, val)
            return

    def encode_port_metric(self, stats_json):
        stats = json.loads(stats_json)        
        metric = otg_pb2.PortMetric()

        if 'name' in stats:
            metric.name = stats['name']
        if 'location' in stats:
            metric.location = stats['location']

        if 'link' in stats:
            if stats['link'] == 'up':
                metric.link = otg_pb2.PortMetric.UP
            if stats['link'] == 'down':
                metric.link = otg_pb2.PortMetric.DOWN
        if 'capture' in stats:
            if stats['capture'] == 'started':            
                metric.capture = otg_pb2.PortMetric.STARTED
            if stats['capture'] == 'stopped':
                metric.capture = otg_pb2.PortMetric.STOPPED

        if 'frames_tx' in stats:
            metric.frames_tx = stats['frames_tx']
        if 'frames_rx' in stats:
            metric.frames_rx =  stats['frames_rx']
        if 'bytes_tx' in stats:
            metric.bytes_tx =  stats['bytes_tx']
        if 'bytes_rx' in stats:
            metric.bytes_rx =  stats['bytes_rx']
        if 'frames_tx_rate' in stats:
            metric.frames_tx_rate =  stats['frames_tx_rate']
        if 'frames_rx_rate' in stats:
            metric.frames_rx_rate =  stats['frames_rx_rate']
        if 'bytes_tx_rate' in stats:
            metric.bytes_tx_rate =  stats['bytes_tx_rate']
        if 'bytes_rx_rate' in stats:
            metric.bytes_rx_rate =  stats['bytes_rx_rate']
        target = Any()
        target.Pack(metric)
        return target

    def encode_flow_metric(self, stats_json):
        stats = json.loads(stats_json)        
        metric = otg_pb2.FlowMetric()    
        if 'name' in stats:
            metric.name = stats['name']
        
        if 'transmit' in stats:
            if stats['transmit'] == 'started':
                metric.transmit = otg_pb2.FlowMetric.STARTED
            if stats['transmit'] == 'stopped':
                metric.transmit = otg_pb2.FlowMetric.STOPPED
            if stats['transmit'] == 'paused':
                metric.transmit = otg_pb2.FlowMetric.PAUSED
        if 'port_tx' in stats:
            metric.port_tx = stats['port_tx']
        if 'port_rx' in stats:
            metric.port_rx = stats['port_rx']
        if 'frames_tx' in stats:
            metric.frames_tx = stats['frames_tx']
        if 'frames_rx' in stats:
            metric.frames_rx = stats['frames_rx']
        if 'bytes_tx' in stats:
            metric.bytes_tx = stats['bytes_tx']
        if 'bytes_rx' in stats:
            metric.bytes_rx = stats['bytes_rx']
        if 'frames_tx_rate' in stats:
            metric.frames_tx_rate = stats['frames_tx_rate']
        if 'frames_rx_rate' in stats:
            metric.frames_rx_rate = stats['frames_rx_rate']
        if 'loss' in stats:
            metric.loss = stats['loss']
        target = Any()
        target.Pack(metric)
        return target

    def encode_protocol_metric(self, stats_json):
        stats = json.loads(stats_json)        
        metric = otg_pb2.Bgpv4Metric()
        
        if 'name' in stats:
            metric.name = stats['name']
        if 'sessions_total' in stats:
            metric.sessions_total = stats['sessions_total']
        if 'sessions_up' in stats:
            metric.sessions_up = stats['sessions_up']
        if 'sessions_down' in stats:
            metric.sessions_down = stats['sessions_down']
        if 'sessions_not_started' in stats:
            metric.sessions_not_started = stats['sessions_not_started']
        if 'routes_advertised' in stats:
            metric.routes_advertised = stats['routes_advertised']
        if 'routes_withdrawn' in stats:
                metric.routes_withdrawn = stats['routes_withdrawn']

        target = Any()
        target.Pack(metric)
        return target

    def compute_delta(self):
        delta = {}
        if self.curr_stats == None:
            self.delta_stats = None
            return

        if self.prev_stats == None:
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
        try:
            if self.init_once == False:
                self.app_mode = options.app_mode
                self.unittest = options.unittest
                self.target_address = options.target_address
                self.logger = logging.getLogger(options.logfile)

                self.api = None
                self.stopped = False

                self.port_subscriptions = {}
                self.flow_subscriptions = {}
                self.protocol_subscriptions = {}
                
                self.lock = Lock()
                self.get_api()
                self.start_worker_threads()
                
                if self.unittest == False:
                    self.setup_test()
                    self.start_test()
                self.init_once = True
                return self.init_once, None
        except Exception as ex:
            return self.init_once, str(ex)
        return self.init_once, None

    def start_worker_threads(self):
        self.logger.info('Starting all collection threads')
        self.flow_stats_thread = Thread(target=self.collect_flow_stats, args=[])
        self.flow_stats_thread.start()        
        self.port_stats_thread = Thread(target=self.collect_port_stats, args=[])
        self.port_stats_thread.start()
        self.protocol_stats_thread = Thread(target=self.collect_protocol_stats, args=[])            
        self.protocol_stats_thread.start()
        
        
    def stop_worker_threads(self):
        self.logger.info('Stopping all collection threads')
        self.stopped = True
        self.flow_stats_thread.join()
        self.port_stats_thread.join()
        self.protocol_stats_thread.join()        

    async def terminate(self, request_iterator):
        self.logger.info('Terminate connection')
        self.stop_worker_threads()
        await self.deregister_subscription(request_iterator)
        self.dump_all_subscription()

    def collect_stats(self, subscriptions, func, meta):
        self.lock.acquire()        
        self._collect_stats(subscriptions, func, meta)
        self.lock.release()

    def _collect_stats(self, subscriptions, func, meta):
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
            self.logger.info('Collect %s stats for %s', meta, names)
            try:
                metrics = func(names)            
                self.logger.info('Collected %s stats for %s', meta, metrics)
                for metric in metrics:
                    if metric.name not in name_to_sub_reverse_map:
                        continue
                    sub = name_to_sub_reverse_map[metric.name]
                    sub.prev_stats = sub.curr_stats
                    sub.curr_stats = metric
                    sub.compute_delta()
                    sub.encode_stats(metric.name)
            except Exception as ex:
                for key in subscriptions:
                    sub.error = str(ex)
            
        except Exception:
            self.logger.error("Fatal error in collecting stats for %s: names:%s", meta, names)
            self.logger.error("Fatal error: ", exc_info=True)
            
            

    
    def collect_flow_stats(self):
        self.logger.info('Started flow stats collection thread')
        while self.stopped == False:
            if len(self.flow_subscriptions) > 0:
                self.collect_stats(self.flow_subscriptions,\
                        self.get_flow_metric, 'Flow')            
            time.sleep(5)
        

    def collect_port_stats(self):
        self.logger.info('Started port stats collection thread')
        while self.stopped == False:
            if len(self.port_subscriptions) > 0:
                self.collect_stats(self.port_subscriptions,\
                        self.get_port_metric, 'Port')            
            time.sleep(5)
        

    def collect_protocol_stats(self):
        time.sleep(6)
        self.logger.info('Started protocol stats collection thread')
        while self.stopped == False:
            if len(self.protocol_subscriptions) > 0:
                self.collect_stats(self.protocol_subscriptions,\
                        self.get_bgpv4_metric, 'Protocol')            
            time.sleep(5)
    
    def get_api(self):
        if self.init_once:
            return self.api
        target = None
        if self.unittest:
            target = "http://{}".format('127.0.0.1:80')
        else:
            target = "https://{}".format(self.target_address)
        self.logger.info('Initializing snappi for %s at target %s', self.app_mode, target)
        # when using ixnetwork extension, host is IxNetwork API Server
        
        if self.app_mode == 'ixnetwork':
            self.api = snappi.api(host=target, ext='ixnetwork')
        else:
            self.api = snappi.api(host=target)
        self.logger.info('Initialized snappi...')
        return self.api
  
    def setup_test(self):
        self.setup_b2b_test()
        #self.setup_dut_test()

    def setup_dut_test(self):
        self.logger.info('Setting up test...')
        jsonRequest = """
        {
            "ports": [
                {
                "location": "10.36.74.135;1;1",
                "name": "P1"
                },
                {
                "location": "10.36.74.135;1;2",
                "name": "P2"
                }
            ],
            "options": {
                "port_options": {
                "location_preemption": true
                }
            },
            "devices": [
                {
                    "container_name": "P1",
                    "device_count": 3,
                    "name": "BGP Router 1",
                    "ethernet": {
                        "name": "Ethernet 1",
                        "ipv4": {
                            "name": "IPv4 1",
                            "bgpv4": {
                                "name": "BGP Peer 1",
                                "router_id": {
                                    "values": [
                                        "2.2.2.2",
                                        "2.2.2.3",
                                        "2.2.2.4"
                                    ],
                                    "choice": "values"
                                },
                                "dut_ipv4_address": {
                                    "choice": "value",
                                    "value": "20.20.20.2"
                                },
                                "as_type": "ibgp",
                                "as_number": {
                                    "choice": "value",
                                    "value": "3000"
                                },
                                "bgpv4_route_ranges" : [
                                    {
                                        "name" : "Network Group 1",
                                        "range_count" : 4,
                                        "address_count" : 1,
                                        "address" : {
                                            "choice": "increment",
                                            "increment": {
                                                "start" : "200.1.0.0",
                                                "step" : "0.1.0.0"
                                            }
                                        }
                                    }
                                ]
                            },
                            "address": {
                                "values": [
                                "20.20.20.11",
                                "20.20.20.12",
                                "20.20.20.13"
                                ],
                                "choice": "values"
                            },
                            "gateway": {
                                "choice": "value",
                                "value": "20.20.20.2"
                            }
                        }
                    }
                },
                {
                    "container_name": "P2",
                    "device_count": 3,
                    "name": "BGP Router 2",
                    "ethernet": {
                        "name": "Ethernet 2",
                        "ipv4": {
                            "name": "IPv4 2",
                            "bgpv4": {
                                "name": "BGP Peer 2",
                                "router_id": {
                                    "values": [
                                        "3.2.2.2",
                                        "3.2.2.3",
                                        "3.2.2.4"
                                    ],
                                    "choice": "values"
                                },
                                "dut_ipv4_address": {
                                    "choice": "value",
                                    "value": "20.20.20.2"
                                },
                                "as_type": "ibgp",
                                "as_number": {
                                    "choice": "value",
                                    "value": "3000"
                                },
                                "bgpv4_route_ranges" : [
                                    {
                                        "name" : "Network Group 2",
                                        "range_count" : 4,
                                        "address_count" : 1,
                                        "address" : {
                                            "choice": "increment",
                                            "increment": {
                                                "start" : "100.1.0.0",
                                                "step" : "0.1.0.0"
                                            }
                                        }
                                    }
                                ]
                            },
                            "address": {
                                "values": [
                                "20.20.20.21",
                                "20.20.20.22",
                                "20.20.20.23"
                                ],
                                "choice": "values"
                            },
                            "gateway": {
                                "choice": "value",
                                "value": "20.20.20.2"
                            }
                        }
                    }
                }
            ],
            "flows": [
                {
                    "name": "F1",
                    "tx_rx": {
                        "choice": "port",
                        "port": {
                            "tx_name": "P1",
                            "rx_name": "P2"
                        }
                    },
                    "size": {
                        "choice": "fixed",
                        "fixed": 1518
                    },
                    "rate": {
                        "choice": "pps",
                        "pps": 5
                    },
                    "duration": {
                        "choice": "continuous"
                    },
                    "packet": [
                        {
                            "choice": "ethernet",
                            "ethernet": {
                                "dst": {
                                    "choice": "value",
                                    "value": "00:00:00:00:00:BB"
                                },
                                "src": {
                                    "choice": "value",
                                    "value": "00:00:00:00:00:AA"
                                }
                            }
                        },
                        {
                            "choice": "ipv4",
                            "ipv4": {
                                "src": {
                                    "choice": "value",
                                    "value": "20.10.0.1"
                                },
                                "dst": {
                                    "choice": "value",
                                    "value": "20.10.0.2"
                                }
                            }
                        }
                    ]
                },
                {
                    "name": "F2",
                    "tx_rx": {
                        "choice": "port",
                        "port": {
                            "tx_name": "P2",
                            "rx_name": "P1"
                        }
                    },
                    "size": {
                        "choice": "fixed",
                        "fixed": 1518
                    },
                    "rate": {
                        "choice": "pps",
                        "pps": 5
                    },
                    "duration": {
                        "choice": "fixed_packets",
                        "fixed_packets": {
                            "packets": 500
                        }
                    },
                    "packet": [
                        {
                            "choice": "ethernet",
                            "ethernet": {
                                "dst": {
                                    "choice": "value",
                                    "value": "00:00:00:00:00:CB"
                                },
                                "src": {
                                    "choice": "value",
                                    "value": "00:00:00:00:00:CA"
                                }
                            }
                        },
                        {
                            "choice": "ipv4",
                            "ipv4": {
                                "src": {
                                    "choice": "value",
                                    "value": "30.10.0.1"
                                },
                                "dst": {
                                    "choice": "value",
                                    "value": "30.10.0.2"
                                }
                            }
                        }
                    ]
                }
            ]
        }
        """

        response = self.api.set_config(jsonRequest)        
        self.logger.info('Setup test done...')

    def setup_b2b_test(self):
        self.logger.info('Setting up test...')
        jsonRequest = """
        {
            "ports": [
                {
                "location": "10.72.47.17;1;1",
                "name": "P1"
                },
                {
                "location": "10.72.47.17;1;2",
                "name": "P2"
                }
            ],
            "options": {
                "port_options": {
                "location_preemption": true
                }
            },
            "devices": [
                {
                    "container_name": "P1",
                    "device_count": 3,
                    "name": "BGP Router 1",
                    "ethernet": {
                        "name": "Ethernet 1",
                        "ipv4": {
                            "name": "IPv4 1",
                            "bgpv4": {
                                "name": "BGP Peer 1",
                                "router_id": {
                                    "values": [
                                        "2.2.2.2",
                                        "2.2.2.3",
                                        "2.2.2.4"
                                    ],
                                    "choice": "values"
                                },
                                "dut_ipv4_address": {
                                    "choice": "values",
                                    "values": [
                                        "20.20.20.21",
                                        "20.20.20.22",
                                        "20.20.20.23"
                                    ],
                                },
                                "as_type": "ibgp",
                                "as_number": {
                                    "choice": "value",
                                    "value": "3000"
                                },
                                "bgpv4_route_ranges" : [
                                    {
                                        "name" : "Network Group 1",
                                        "range_count" : 4,
                                        "address_count" : 1,
                                        "address" : {
                                            "choice": "increment",
                                            "increment": {
                                                "start" : "200.1.0.0",
                                                "step" : "0.1.0.0"
                                            }
                                        }
                                    }
                                ]
                            },
                            "address": {
                                "values": [
                                "20.20.20.11",
                                "20.20.20.12",
                                "20.20.20.13"
                                ],
                                "choice": "values"
                            },
                            "gateway": {
                                "choice": "values",
                                "values": [
                                    "20.20.20.21",
                                    "20.20.20.22",
                                    "20.20.20.23"
                                ],
                            }
                        }
                    }
                },
                {
                    "container_name": "P2",
                    "device_count": 3,
                    "name": "BGP Router 2",
                    "ethernet": {
                        "name": "Ethernet 2",
                        "ipv4": {
                            "name": "IPv4 2",
                            "bgpv4": {
                                "name": "BGP Peer 2",
                                "router_id": {
                                    "values": [
                                        "3.2.2.2",
                                        "3.2.2.3",
                                        "3.2.2.4"
                                    ],
                                    "choice": "values"
                                },
                                "dut_ipv4_address": {
                                    "values": [
                                        "20.20.20.11",
                                        "20.20.20.12",
                                        "20.20.20.13"
                                    ],
                                    "choice": "values"
                                },
                                "as_type": "ibgp",
                                "as_number": {
                                    "choice": "value",
                                    "value": "3000"
                                },
                                "bgpv4_route_ranges" : [
                                    {
                                        "name" : "Network Group 2",
                                        "range_count" : 4,
                                        "address_count" : 1,
                                        "address" : {
                                            "choice": "increment",
                                            "increment": {
                                                "start" : "100.1.0.0",
                                                "step" : "0.1.0.0"
                                            }
                                        }
                                    }
                                ]
                            },
                            "address": {
                                "values": [
                                "20.20.20.21",
                                "20.20.20.22",
                                "20.20.20.23"
                                ],
                                "choice": "values"
                            },
                            "gateway": {
                                "values": [
                                    "20.20.20.11",
                                    "20.20.20.12",
                                    "20.20.20.13"
                                ],
                                "choice": "values"
                            }
                        }
                    }
                }
            ],
            "flows": [
                {
                    "name": "F1",
                    "tx_rx": {
                        "choice": "port",
                        "port": {
                            "tx_name": "P1",
                            "rx_name": "P2"
                        }
                    },
                    "size": {
                        "choice": "fixed",
                        "fixed": 1518
                    },
                    "rate": {
                        "choice": "pps",
                        "pps": 5
                    },
                    "duration": {
                        "choice": "continuous"
                    },
                    "packet": [
                        {
                            "choice": "ethernet",
                            "ethernet": {
                                "dst": {
                                    "choice": "value",
                                    "value": "00:00:00:00:00:BB"
                                },
                                "src": {
                                    "choice": "value",
                                    "value": "00:00:00:00:00:AA"
                                }
                            }
                        },
                        {
                            "choice": "ipv4",
                            "ipv4": {
                                "src": {
                                    "choice": "value",
                                    "value": "20.10.0.1"
                                },
                                "dst": {
                                    "choice": "value",
                                    "value": "20.10.0.2"
                                }
                            }
                        }
                    ]
                },
                {
                    "name": "F2",
                    "tx_rx": {
                        "choice": "port",
                        "port": {
                            "tx_name": "P2",
                            "rx_name": "P1"
                        }
                    },
                    "size": {
                        "choice": "fixed",
                        "fixed": 1518
                    },
                    "rate": {
                        "choice": "pps",
                        "pps": 5
                    },
                    "duration": {
                        "choice": "fixed_packets",
                        "fixed_packets": {
                            "packets": 500
                        }
                    },
                    "packet": [
                        {
                            "choice": "ethernet",
                            "ethernet": {
                                "dst": {
                                    "choice": "value",
                                    "value": "00:00:00:00:00:CB"
                                },
                                "src": {
                                    "choice": "value",
                                    "value": "00:00:00:00:00:CA"
                                }
                            }
                        },
                        {
                            "choice": "ipv4",
                            "ipv4": {
                                "src": {
                                    "choice": "value",
                                    "value": "30.10.0.1"
                                },
                                "dst": {
                                    "choice": "value",
                                    "value": "30.10.0.2"
                                }
                            }
                        }
                    ]
                }
            ]
        }
        """

        response = self.api.set_config(jsonRequest)        
        self.logger.info('Setup test done...')

    def start_test(self):
        jsonRequest = """
                {
                    "flow_names": null,
                    "state" : "start"
                }
           """
        self.api.set_transmit_state(jsonRequest)

    def get_flow_metric(self, flow_names, stat_names=None):         
        api = self.get_api()        
        req = api.metrics_request()
        req.flow.flow_names = flow_names        
        res = api.get_metrics(req)
        return res.flow_metrics

    def get_port_metric(self, port_names, stat_names=None):
        api = self.get_api()        
        req = api.metrics_request()
        req.port.port_names = port_names
        res = api.get_metrics(req)
        return res.port_metrics
    
    def get_bgpv6_metric(self, device_names, stat_names=None):
        api = self.get_api()        
        req = api.metrics_request()
        req.bgpv6.device_names = device_names
        res = api.get_metrics(req)
        return res.bgpv6_metrics

    def get_bgpv4_metric(self, device_names, stat_names=None):
        api = self.get_api()        
        req = api.metrics_request()
        #req.bgpv4.device_names = device_names
        req.bgpv4.device_names = [] # [] gets all stats
        res = api.get_metrics(req)
        return res.bgpv4_metrics
    
    def create_update_response(self, encoding, stats_name, stats):
        
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
        notification = gnmi_pb2.Notification(timestamp=milliseconds, update=[update])
        sub_res = gnmi_pb2.SubscribeResponse(update=notification)
        return sub_res

    def create_error_response(self, stats_name, error_message):
        #err = gnmi_pb2.Error(data=stats_name, message=error_message)
        err = gnmi_pb2.Error(message=stats_name + ': ' + error_message)
        err_res = gnmi_pb2.SubscribeResponse(error=err)
        return err_res

    def dump_all_subscription(self):
        
        self.logger.info('Port Subscriptions: total subscription = %s', len(self.port_subscriptions))
        for path in self.port_subscriptions:
            sub = self.port_subscriptions[path]
            self.logger.info('\t\tSubscriptions: %s, Name: %s', path, sub.name)

        self.logger.info('Flow Subscriptions: total subscription = %s', len(self.flow_subscriptions))
        for path in self.flow_subscriptions:
            sub = self.flow_subscriptions[path]
            self.logger.info('\t\tSubscriptions: %s, Name: %s', path, sub.name)

        self.logger.info('Protocol Subscriptions: total subscription = %s', len(self.protocol_subscriptions))
        for path in self.protocol_subscriptions:
            sub = self.protocol_subscriptions[path]
            self.logger.info('\t\tSubscriptions: %s, Name: %s', path, sub.name)
                
    async def register_subscription(self, request_iterator):
        try:
            async for request in request_iterator.__aiter__():  
                if request == None:
                    continue
                for subscription in request.subscribe.subscription:
                    sub = SubscriptionReq(request.subscribe, subscription)
                    sub.encoding = request.subscribe.encoding
                    if sub.type == RequestType.PORT:
                        self.port_subscriptions[sub.stringpath] = sub
                    elif sub.type == RequestType.FLOW:
                        self.flow_subscriptions[sub.stringpath] = sub
                    elif sub.type == RequestType.PROTOCOL:
                        self.protocol_subscriptions[sub.stringpath] = sub
                    else:
                        self.logger.info('Unknown Subscription %s', sub.stringpath)
        except Exception as ex:
            self.logger.error('Exception: %s', str(ex))
            self.logger.error('Exception: ', exc_info=True)   

        self.dump_all_subscription()

    async def deregister_subscription(self, subscriptions):
        async for request in request_iterator.__aiter__():  
            for subscription in request.subscribe.subscription:                
                sub = SubscriptionReq(subscribe, subscription)
                if sub.type == RequestType.PORT:
                    self.port_subscriptions.pop(sub.stringpath)
                elif sub.type == RequestType.FLOW:
                    self.flow_subscriptions.pop(sub.stringpath)
                elif sub.type == RequestType.PROTOCOL:
                    self.protocol_subscriptions.pop(sub.stringpath)
        self.dump_all_subscription()
        self.stop_worker_threads()
    
    async def publish_stats(self):
        results = []

        def publish(key, subscriptions, res, meta=None):
            #self.logger.info('Publish %s Stats %s', meta, key)
            sub = subscriptions[key]
            
            if sub.error != None:
                res.append(self.create_error_response(sub.name, sub.error))
                return
            
            if sub.encoded_stats != None:
                res.append(sub.encoded_stats)

        for key in self.port_subscriptions:
            publish(key, self.port_subscriptions, results, 'Port')

        for key in self.flow_subscriptions:
            publish(key, self.flow_subscriptions, results, 'Flow')

        for key in self.protocol_subscriptions:
            publish(key, self.protocol_subscriptions, results, 'Protocol')
        
        return results
        
    async def keep_polling(self):
        return self.stopped == False


#if __name__ == 'main':
#setup_test()

