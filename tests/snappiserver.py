import json
import multiprocessing
import time

import requests
import snappi
from flask import Flask, Response, request
from otg_gnmi.common.utils import init_logging, get_current_time

from tests.utils.common import get_mockserver_status
from tests.utils.settings import MockConfig

app = Flask(__name__)
CONFIG = MockConfig()

logfile = 'flask'+'-'+str(get_current_time())+'.log'
flask_logger = init_logging(
    'test',
    'mockserver',
    logfile
)


@app.route('/status', methods=['GET'])
def get_status():
    return Response(
        status=200,
        response=json.dumps({'status': 'up'}),
        headers={'Content-Type': 'application/json'})


@app.route('/config', methods=['POST'])
def set_config():
    global CONFIG
    config = snappi.api().config()
    config.deserialize(request.data.decode('utf-8'))
    test = config.options.port_options.location_preemption
    if test is not None and isinstance(test, bool) is False:
        return Response(status=590,
                        response=json.dumps({'detail': 'invalid data type'}),
                        headers={'Content-Type': 'application/json'})
    else:
        status = get_mockserver_status()
        if status == "200":
            CONFIG = config
            return Response(status=200,
                            response=json.dumps({'warnings': []}),
                            headers={'Content-Type': 'application/json'})
        elif status == "200-warning":
            CONFIG = config
            return Response(status=200,
                            response=json.dumps(
                                {'warnings': ['mock 200 set_config warning']}),
                            headers={'Content-Type': 'application/json'})
        elif status == "400":
            return Response(status=400,
                            response=json.dumps(
                                {'errors': ['mock 400 set_config error']}),
                            headers={'Content-Type': 'application/json'})
        elif status == "500":
            return Response(status=500,
                            response=json.dumps(
                                {'errors': ['mock 500 set_config error']}),
                            headers={'Content-Type': 'application/json'})
        else:
            return Response(status=501,
                            response=json.dumps(
                                {'errors': ['set_config is not implemented']}),
                            headers={'Content-Type': 'application/json'})


@app.route('/config', methods=['GET'])
def get_config():
    global CONFIG
    status = get_mockserver_status()
    if status in ["200",  "200-warning"]:
        return Response(CONFIG.serialize() if CONFIG is not None else '{}',
                        mimetype='application/json',
                        status=200)
    elif status == "400":
        return Response(status=400,
                        response=json.dumps(
                            {'errors': ['mock 400 get_config error']}),
                        headers={'Content-Type': 'application/json'})
    elif status == "500":
        return Response(status=500,
                        response=json.dumps(
                            {'errors': ['mock 500 get_config error']}),
                        headers={'Content-Type': 'application/json'})
    else:
        return Response(status=501,
                        response=json.dumps(
                            {'errors': ['get_config is not implemented']}),
                        headers={'Content-Type': 'application/json'})


@app.route('/results/metrics', methods=['POST'])
def get_metrics():
    status = get_mockserver_status()
    global CONFIG
    if status in ["200", "200-warning"]:
        api = snappi.api()
        metrics_request = api.metrics_request()
        metrics_request.deserialize(request.data.decode('utf-8'))
        metrics_response = api.metrics_response()
        if metrics_request.choice == 'port':
            for metric in CONFIG.port_metrics:
                metrics_response.port_metrics.metric(
                    name=metric['name'],
                    frames_tx=10000,
                    frames_rx=10000
                )
        elif metrics_request.choice == 'flow':
            for metric in CONFIG.flow_metrics:
                metrics_response.flow_metrics.metric(
                    name=metric['name'],
                    port_tx="P1",
                    port_rx="P2",
                    frames_tx=10000,
                    frames_rx=10000
                )

        elif metrics_request.choice == 'bgpv4':
            for metric in CONFIG.bgpv4_metrics:
                metrics_response.bgpv4_metrics.metric(
                    name=metric['name'],
                    session_state=metric["session_state"],
                    session_flap_count=0,
                    routes_advertised=1000,
                    routes_received=500
                )

        elif metrics_request.choice == 'bgpv6':
            for metric in CONFIG.bgpv6_metrics:
                metrics_response.bgpv6_metrics.metric(
                    name=metric['name'],
                    session_state=metric["session_state"],
                    session_flap_count=0,
                    routes_advertised=1000,
                    routes_received=500
                )

        elif metrics_request.choice == 'isis':
            for metric in CONFIG.isis_metrics:
                metrics_response.isis_metrics.metric(
                    name=metric['name'],
                    l1_sessions_up=metric["l1_sessions_up"],
                )

        return Response(metrics_response.serialize(),
                        mimetype='application/json',
                        status=200)
    elif status == "400":
        return Response(status=400,
                        response=json.dumps(
                            {'errors': ['mock 400 get_metrics error']}),
                        headers={'Content-Type': 'application/json'})
    elif status == "500":
        return Response(status=500,
                        response=json.dumps(
                            {'errors': ['mock 500 get_metrics error']}),
                        headers={'Content-Type': 'application/json'})
    else:
        return Response(status=501,
                        response=json.dumps(
                            {'errors': ['get_metrics is not implemented']}),
                        headers={'Content-Type': 'application/json'})


@app.route('/results/states', methods=['POST'])
def get_states():
    status = get_mockserver_status()
    global CONFIG
    if status in ["200", "200-warning"]:
        api = snappi.api()
        states_request = api.states_request()
        states_request.deserialize(request.data.decode('utf-8'))
        flask_logger.info('get_status Request : [%s]', states_request)

        states_response = api.states_response()
        if states_request.choice == 'ipv4_neighbors':
            states_response.choice = 'ipv4_neighbors'
            for state in CONFIG.ipv4_neighbors:
                states_response.ipv4_neighbors.state(
                    ethernet_name=state['ethernet_name'],
                    ipv4_address=state['ipv4_address'],
                    link_layer_address="aa:bb:cc:dd:ee:ff"
                )
        elif states_request.choice == 'ipv6_neighbors':
            states_response.choice = 'ipv6_neighbors'
            for state in CONFIG.ipv6_neighbors:
                states_response.ipv6_neighbors.state(
                    ethernet_name=state['ethernet_name'],
                    ipv6_address=state['ipv6_address'],
                    link_layer_address="aa:bb:cc:dd:ee:ff"
                )

        flask_logger.info('get_status Responese : [%s]', states_response)

        return Response(states_response.serialize(),
                        mimetype='application/json',
                        status=200)
    elif status == "400":
        return Response(status=400,
                        response=json.dumps(
                            {'errors': ['mock 400 get_states error']}),
                        headers={'Content-Type': 'application/json'})
    elif status == "500":
        return Response(status=500,
                        response=json.dumps(
                            {'errors': ['mock 500 get_states error']}),
                        headers={'Content-Type': 'application/json'})
    else:
        return Response(status=501,
                        response=json.dumps(
                            {'errors': ['get_states is not implemented']}),
                        headers={'Content-Type': 'application/json'})


@app.after_request
def after_request(resp):
    print(request.method, request.url, ' -> ', resp.status)
    return resp


def web_server():
    app.run(port=11020, debug=True, use_reloader=False)


class SnappiServer(object):
    def __init__(self):
        self._CONFIG = None

    def start(self):
        self._web_server_thread = multiprocessing.Process(
            target=web_server, args=())
        self._web_server_thread.start()
        self._wait_until_ready()
        return self

    def stop(self):
        self._web_server_thread.terminate()

    def _wait_until_ready(self):
        while True:
            try:
                r = requests.get(url='http://127.0.0.1:11020/status')
                res = r.json()
                if res['status'] != 'up':
                    raise Exception('waiting for SnappiServer to be up')
                break
            except Exception as e:
                print(e)
                pass
            time.sleep(.1)
