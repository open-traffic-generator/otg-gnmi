from flask import Flask, request, Response
import threading
import json
import time
import snappi
import logging
from tests.utils.settings import *
from otg_gnmi.common.utils import *

app = Flask(__name__)
CONFIG = GnmiTestSettings()

logfile = init_logging('flask')
flask_logger = logging.getLogger(logfile)

'''
# push one-arm config
curl -kLX POST https://localhost/config -d @tests/configs/basic_unidir_ethernet.json -H "Content-Type: application/json"
# or push two-arm config
curl -kLX POST https://localhost/config -d @tests/configs/basic_ethernet.json -H "Content-Type: application/json"
# start transmit
curl -kLX POST https://localhost/control/transmit -H  "Content-Type: application/json" -d "{"state": "start"}"
# fetch all port metrics
curl -kLX POST "https://localhost/results/metrics" -H  "Content-Type: application/json" -d "{"choice": "port", "port": {}}"
# fetch some flow metrics (empty result in one-arm scenario - known issue)
curl -kLX POST "https://localhost/results/metrics" -H  "Content-Type: application/json" -d "{"choice": "flow", "flow": {"flow_names": ["f1"]}}"
'''


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


@app.route('/control/transmit', methods=['POST'])
def set_transmit_state():
    global CONFIG
    return Response(status=200)


@app.route('/results/metrics', methods=['POST'])
def get_metrics():
    global CONFIG
    api = snappi.api()

    metrics_request = api.metrics_request()
    metrics_request.deserialize(request.data.decode('utf-8'))
    flask_logger.info('get_metrics() -> %s', request.data.decode('utf-8'))
    metrics_response = api.metrics_response()
    if metrics_request.choice == 'port':
        for port in CONFIG.ports:
            metrics_response.port_metrics.metric(
                name=port['name'], frames_tx=10000, frames_rx=10000
            )
    elif metrics_request.choice == 'flow':
        for flow in CONFIG.flows:
            metrics_response.flow_metrics.metric(
                name=flow.name, frames_tx=10000, frames_rx=10000
            )

    return Response(metrics_response.serialize(),
                    mimetype='application/json',
                    status=200)

@app.after_request
def after_request(resp):
    print(request.method, request.url, ' -> ', resp.status)
    return resp


def web_server():
    app.run(port=80, debug=True, use_reloader=False)


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
        flask_logger.info('Init snappi api object ')
        api = snappi.api(host='http://127.0.0.1:80')
        flask_logger.info('Done Init snappi api object ')
        while True:
            try:
                conf = api.get_config()
                flask_logger.info ('Confing: %s', conf)
                break
            except Exception:
                pass
            time.sleep(.1)


if __name__ == '__main__':
    server = SnappiServer()
    flask_logger.info('Server: %s', server)    
    server.run()
    server._web_server_thread.join()