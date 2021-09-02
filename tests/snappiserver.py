from flask import Flask, request, Response
import threading
import json
import time
import snappi
import logging
import requests
from tests.utils.settings import *
from otg_gnmi.common.utils import *

app = Flask(__name__)
CONFIG = MockConfig()

logfile = init_logging('flask')
flask_logger = logging.getLogger(logfile)

'''
# push one-arm config
curl -kLX POST https://localhost/config -d @tests/configs/basic_unidir_ethernet.json -H "Content-Type: application/json"
# or push two-arm config
curl -kLX POST https://localhost/config -d @tests/configs/basic_ethernet.json -H "Content-Type: application/json"
# fetch all port metrics
curl -kLX POST "https://localhost/results/metrics" -H  "Content-Type: application/json" -d "{"choice": "port", "port": {}}"
# fetch some flow metrics (empty result in one-arm scenario - known issue)
curl -kLX POST "https://localhost/results/metrics" -H  "Content-Type: application/json" -d "{"choice": "flow", "flow": {"flow_names": ["f1"]}}"
'''


@app.route('/status', methods=['GET'])
def get_status():
    return Response(status=200,
                    response=json.dumps({'status': 'up'}),
                    headers={'Content-Type': 'application/json'})


@app.route('/config', methods=['POST'])
def set_config():
    global CONFIG
    config = snappi.api().config()
    config.deserialize(request.data.decode('utf-8'))
    flask_logger.info('set_config() -> %s', request.data.decode('utf-8'))
    test = config.options.port_options.location_preemption
    if test is not None and isinstance(test, bool) is False:
        return Response(status=590,
                        response=json.dumps({'detail': 'invalid data type'}),
                        headers={'Content-Type': 'application/json'})
    else:
        CONFIG = config
        return Response(status=200)


@app.route('/config', methods=['GET'])
def get_config():
    global CONFIG
    flask_logger.info('get_config() -> %s', CONFIG.serialize())
    return Response(CONFIG.serialize() if CONFIG is not None else '{}',
                    mimetype='application/json',
                    status=200)


@app.route('/results/metrics', methods=['POST'])
def get_metrics():
    global CONFIG
    api = snappi.api()

    metrics_request = api.metrics_request()
    flask_logger.info('get_metrics() -> %s', request.data.decode('utf-8'))
    metrics_request.deserialize(request.data.decode('utf-8'))
    metrics_response = api.metrics_response()
    if metrics_request.choice == 'port':
        for metric in CONFIG.port_metrics:
            metrics_response.port_metrics.metric(
                name=metric['name'], frames_tx=10000, frames_rx=10000
            )
    elif metrics_request.choice == 'flow':
        for metric in CONFIG.flow_metrics:
            metrics_response.flow_metrics.metric(
                name=metric['name'], port_tx="P1", port_rx="P2", frames_tx=10000, frames_rx=10000
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

    return Response(metrics_response.serialize(),
                    mimetype='application/json',
                    status=200)


@app.after_request
def after_request(resp):
    print(request.method, request.url, ' -> ', resp.status)
    return resp


def web_server():
    app.run(port=11009, debug=True, use_reloader=False)


class SnappiServer(object):
    def __init__(self):
        self._CONFIG = None
        flask_logger.info('Init SnappiServer')

    def run(self):
        flask_logger.info('Starting web server')
        self._web_server_thread = threading.Thread(target=web_server)
        self._web_server_thread.setDaemon(True)
        self._web_server_thread.start()
        flask_logger.info('Started web server')
        self._wait_until_ready()

    def _wait_until_ready(self):
        while True:
            try:
                r = requests.get(url='http://127.0.0.1:11009/status')
                res = r.json()
                if res['status'] != 'up':
                    raise Exception('waiting for SnappiServer to be up')
                break
            except Exception as e:
                print(e)
                pass
            time.sleep(.1)


if __name__ == '__main__':
    server = SnappiServer()
    flask_logger.info('Server: %s', server)
    server.run()
    server._web_server_thread.join()
