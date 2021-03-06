import argparse
import json
import os
import subprocess
import time

import grpc
import mock
from google.protobuf import json_format
from otg_gnmi.autogen import gnmi_pb2
from otg_gnmi.gnmi_serv_asyncio import AsyncGnmiService
from tests.session import Session
from tests.utils.client_utils import generate_subscription_request
from tests.utils.settings import GnmiSettings

SETTINGS_FILE = 'settings.json'
TESTS_FOLDER = 'tests'
OPTIONS = GnmiSettings()
SUDO_USER = "root"


def exec_shell(cmd, sudo=True, check_return_code=True):
    """
    Executes a command in native shell and returns output as str on success or,
    None on error.
    """
    if not sudo:
        cmd = 'sudo -u ' + SUDO_USER + ' ' + cmd

    print('Executing `%s` ...' % cmd)
    p = subprocess.Popen(
        cmd.encode('utf-8', errors='ignore'),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    out, _ = p.communicate()
    out = out.decode('utf-8', errors='ignore')

    print('Output:\n%s' % out)

    if check_return_code:
        if p.returncode == 0:
            return out
        return None
    else:
        return out


def get_pid_of_gnmi_processes():
    print("Getting existing gNMI server process ids...")
    process_ids = []
    out_lines = exec_shell("ps -ef")
    if out_lines is None:
        raise Exception("Failed to get process details!!!")

    out_lines = out_lines.split("\n")

    for line in out_lines:
        if "python -m otg_gnmi" in line:
            print("GNMI process : {}".format(line))
            process_ids.append(line.split()[1])

    print("Process IDs for gnmi processes : {}".format(process_ids))

    return process_ids


def kill_gnmi_processes():
    print("Killing existing gNMI server processes...")
    processes_to_be_killed = get_pid_of_gnmi_processes()

    for process in processes_to_be_killed:
        out = exec_shell("kill -9 {}".format(
            process
        ))

        if out is None:
            raise Exception("Failed to kill process!!!")

        print("Process {} killed...".format(process))


def convert_proto_to_json(proto_obj):
    json_obj = json.loads(
        json_format.MessageToJson(
            proto_obj,
            including_default_value_fields=False,
            preserving_proto_field_name=True
        )
    )

    return json_obj


def get_mockserver_status():
    tests_dir = os.getcwd()
    if 'tests' not in tests_dir:
        tests_dir = os.path.join(tests_dir, 'tests')
    else:
        tests_dir = os.path.split('tests')[0]

    mockstatus_file = os.path.join(tests_dir, 'mockstatus.txt')
    if os.path.exists(mockstatus_file):
        f = open(mockstatus_file, 'r')
        status = f.read()
        f.close()
        print("Current MockServer Status: {}".format(status))
        return status.strip()
    else:
        status = '200'
        print("Current MockServer Status: {}".format(status))
        return status.strip()


def get_parsed_args(op_val):
    parser = argparse.ArgumentParser()
    parser.add_argument('--server-port', help='gRPC server port number',
                        default=50052,
                        type=int)
    parser.add_argument('--app-mode', help='target Application mode)',
                        choices=['ixnetwork', 'athena'],
                        default='ixnetwork',
                        type=str)
    parser.add_argument('--target-host', help='target host address',
                        default='localhost',
                        )
    parser.add_argument('--target-port', help='target port number',
                        default=11020,
                        type=int)
    parser.add_argument('--unittest', help='set to true if running unit test',
                        action='store_true')
    parser.add_argument('--logfile',
                        help='logfile name [date and time auto appended]',
                        default='gNMIServer',
                        type=str)
    parser.add_argument('--no-stdout',
                        help='do not show log on stdout',
                        default=True,
                        action='store_true')
    parser.add_argument('--insecure',
                        help='disable TSL security, by defualt enabled',
                        action='store_true')
    parser.add_argument('--server-key',
                        help='path to private key, default is server.key',
                        default='server.key',
                        type=str)
    parser.add_argument('--server-crt',
                        help='path to certificate key, default is server.crt',
                        default='server.crt',
                        type=str)

    arg_inputs = []
    for op, val in list(op_val.items()):
        if isinstance(val, bool):
            if val:
                arg_inputs.append('--{}'.format(op))
        else:
            arg_inputs.append('--{}'.format(op))
            arg_inputs.append('{}'.format(val))

    args = parser.parse_args(arg_inputs)
    return args


def change_mockserver_status(error_code=200, with_warning=False):
    status = str(error_code)
    if with_warning:
        status += "-warning"
    tests_dir = os.getcwd()
    if 'tests' not in tests_dir:
        tests_dir = os.path.join(tests_dir, 'tests')
    else:
        tests_dir = os.path.split('tests')[0]

    mockstatus_file = os.path.join(tests_dir, 'mockstatus.txt')
    f = open(mockstatus_file, 'w')
    f.write(status)
    f.close()
    print("MockServer Status Set To: {}".format(status))


def get_root_dir():
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def get_settings_file_path():
    tests_dir = get_root_dir()
    if not tests_dir.endswith(TESTS_FOLDER):
        tests_dir = os.path.join(tests_dir, TESTS_FOLDER)
    return os.path.join(tests_dir, SETTINGS_FILE)


def get_mockserver_settings():
    print('Fetching Mock Config from settings.json')
    file_path = get_settings_file_path()
    with open(file_path, 'r') as fp:
        mock_config = json.load(fp)
    return mock_config


def init_gnmi_with_mock_server(error_code=200,
                               with_warning=False):
    print('Intializing gNMI server api......')
    change_mockserver_status(error_code, with_warning)
    mock_config = get_mockserver_settings()
    mock_config_args = get_parsed_args(mock_config)
    print(mock_config_args)
    gnmi_api = AsyncGnmiService(mock_config_args)
    return gnmi_api


async def set(api):
    print('Set gNMI Request......')
    path = gnmi_pb2.Path(elem=[
        gnmi_pb2.PathElem(name='val', key={'name': 'setup_test'})
        ])
    update = gnmi_pb2.Update(
        path=path, val=gnmi_pb2.TypedValue(
            json_val=json.dumps({'name': 'setup_test'}).encode("utf-8")))
    updates = []
    updates.append(update)
    request = gnmi_pb2.SetRequest(update=updates)
    mock_context = mock.create_autospec(spec=grpc.aio.ServicerContext)
    response = await api.Set(request, mock_context)
    results = [x async for x in response]
    return results


async def get(api):
    print('Get gNMI Request......')
    request = gnmi_pb2.GetRequest()
    mock_context = mock.create_autospec(spec=grpc.aio.ServicerContext)
    response = await api.Get(request, mock_context)
    results = [x async for x in response]
    return results


async def capabilities(api):
    print('capabilities gNMI Request......')
    request = gnmi_pb2.CapabilityRequest()
    mock_context = mock.create_autospec(spec=grpc.aio.ServicerContext)
    response = await api.Capabilities(request, mock_context)
    json_res = convert_proto_to_json(response)
    return json_res


async def subscribe(api):
    print('subscribe gNMI Request......')
    request_iterator = generate_subscription_request(OPTIONS)
    mock_context = mock.create_autospec(spec=grpc.aio.ServicerContext)
    mock_context.metadata = OPTIONS.metadata
    responses = api.Subscribe(request_iterator, mock_context)
    count = 0
    response_list = []
    async for response in responses:
        count += 1
        response_list.append(response)
        if count == 3:
            break
    return response_list


def create_new_session(wait_for_responses=3):
    print("Spawning new gNMI client...")
    session = Session()
    session.options.waitForResponses = wait_for_responses
    return session


def crate_new_gnmi_server():
    print("Spawning new gNMI server...")
    kill_gnmi_processes()
    gnmi_server = subprocess.Popen(
        [
            "python",
            "-m",
            "otg_gnmi",
            "--server-port",
            "50135",
            "--app-mode",
            "athena",
            "--unittest",
            "--insecure",
            "--no-stdout"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # Give the server time to start
    time.sleep(2)
    return gnmi_server


def kill_gnmi_server(gnmi_server):
    print("Terminating gNMI server...")
    gnmi_server.terminate()
    kill_gnmi_processes()
    # Give the server time to be closed
    time.sleep(1)
