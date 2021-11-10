import pytest
from tests.utils.common import init_gnmi_with_mock_server, get, set, capabilities, subscribe, change_mockserver_status# noqa
import json


@pytest.mark.asyncio
async def test_gnmi_server_capabilities_api(snappiserver,
                                            gnmi_server):
    gnmi_api = init_gnmi_with_mock_server(200)

    expected_res = {
        'supported_models': [
            {
                'name': 'open-traffic-generator',
                'organization': 'otg',
                'version': '0.0.1'
            }
        ],
        'supported_encodings': [
            'JSON',
            'JSON_IETF',
            'PROTO'
        ],
        'gNMI_version': '0.0.1'
    }
    res = await capabilities(gnmi_api)

    assert res == expected_res


@pytest.mark.asyncio
async def test_gnmi_server_subscribe_api_200(snappiserver,
                                             gnmi_server):
    gnmi_api = init_gnmi_with_mock_server(200)
    responses = await subscribe(gnmi_api)

    expected_names = [
        "P1",
        "P2",
        "F1",
        'BGPv4-1',
        'BGPv6-1',
        'ISIS-1',
        "p1d1eth1",
        "p1d2eth1"
    ]

    expected_stats = [
        {
            'name': 'P1',
            'frames_tx': 10000,
            'frames_rx': 10000
        },
        {
            'name': 'P2',
            'frames_tx': 10000,
            'frames_rx': 10000
        },
        {
            'name': 'F1',
            'port_tx': "P1",
            'port_rx': "P2",
            'frames_tx': 10000,
            'frames_rx': 10000
        },
        {
            'name': 'BGPv4-1',
            'session_state': "down",
            'session_flap_count': 0,
            'routes_advertised': 1000,
            'routes_received': 500
        },
        {
            'name': 'BGPv6-1',
            'session_state': "up",
            'session_flap_count': 0,
            'routes_advertised': 1000,
            'routes_received': 500
        },
        {
            'name': 'ISIS-1',
            'l1_sessions_up': 0
        },
        {
            'ethernet_name': 'p1d1eth1',
            'ipv4_address': '100.100.100.2',
            'link_layer_address' : 'aa:bb:cc:dd:ee:ff'
        },
        {
            'ethernet_name': 'p1d2eth1',
            'ipv6_address': '00:00:00:aa::2',
            'link_layer_address' : 'aa:bb:cc:dd:ee:ff'
        }
    ]

    res_1 = responses[0]
    print(res_1)
    assert res_1.HasField('update')
    assert res_1.update.update[0].path.elem[0].key['name'] in expected_names
    stat_1 = json.loads(res_1.update.update[0].val.json_val.decode('utf-8'))
    assert stat_1 in expected_stats

    res_2 = responses[1]
    assert res_2.HasField('update')
    assert res_2.update.update[0].path.elem[0].key['name'] in expected_names
    stat_2 = json.loads(res_2.update.update[0].val.json_val.decode('utf-8'))
    assert stat_2 in expected_stats

    res_3 = responses[2]
    assert res_3.HasField('update')
    assert res_3.update.update[0].path.elem[0].key['name'] in expected_names
    stat_3 = json.loads(res_3.update.update[0].val.json_val.decode('utf-8'))
    assert stat_3 in expected_stats


@pytest.mark.asyncio
async def test_gnmi_server_subscribe_api_400(snappiserver,
                                             gnmi_server):
    gnmi_api = init_gnmi_with_mock_server(400)
    responses = await subscribe(gnmi_api)

    expected_error_msg = [
        "P1: (400, {\'errors\': [\'mock 400 get_metrics error\']})",
        "P2: (400, {\'errors\': [\'mock 400 get_metrics error\']})",
        "F1: (400, {\'errors\': [\'mock 400 get_metrics error\']})",
        "BGPv4-1: (400, {\'errors\': [\'mock 400 get_metrics error\']})",
        "BGPv6-1: (400, {\'errors\': [\'mock 400 get_metrics error\']})",
        "ISIS-1: (400, {\'errors\': [\'mock 400 get_metrics error\']})",
        "p1d1eth1: (400, {\'errors\': [\'mock 400 get_states error\']})",
        "p1d2eth1: (400, {\'errors\': [\'mock 400 get_states error\']})"
    ]

    for res in responses:
        assert res.HasField('error')
        assert res.error.message in expected_error_msg

    change_mockserver_status(200, False)


@pytest.mark.asyncio
async def test_gnmi_server_subscribe_api_500(snappiserver,
                                             gnmi_server):
    gnmi_api = init_gnmi_with_mock_server(500)
    responses = await subscribe(gnmi_api)

    expected_error_msg = [
        "P1: (500, {\'errors\': [\'mock 500 get_metrics error\']})",
        "P2: (500, {\'errors\': [\'mock 500 get_metrics error\']})",
        "F1: (500, {\'errors\': [\'mock 500 get_metrics error\']})",
        "BGPv4-1: (500, {\'errors\': [\'mock 500 get_metrics error\']})",
        "BGPv6-1: (500, {\'errors\': [\'mock 500 get_metrics error\']})",
        "ISIS-1: (500, {\'errors\': [\'mock 500 get_metrics error\']})",
        "p1d1eth1: (500, {\'errors\': [\'mock 500 get_states error\']})",
        "p1d2eth1: (500, {\'errors\': [\'mock 500 get_states error\']})"
    ]

    for res in responses:
        assert res.HasField('error')
        assert res.error.message in expected_error_msg

    change_mockserver_status(200, False)


@pytest.mark.asyncio
async def test_gnmi_server_subscribe_api_501(snappiserver,
                                             gnmi_server):
    gnmi_api = init_gnmi_with_mock_server(501)
    responses = await subscribe(gnmi_api)

    expected_error_msg = [
        "P1: (501, {\'errors\': [\'get_metrics is not implemented\']})",
        "P2: (501, {\'errors\': [\'get_metrics is not implemented\']})",
        "F1: (501, {\'errors\': [\'get_metrics is not implemented\']})",
        "BGPv4-1: (501, {\'errors\': [\'get_metrics is not implemented\']})",
        "BGPv6-1: (501, {\'errors\': [\'get_metrics is not implemented\']})",
        "ISIS-1: (501, {\'errors\': [\'get_metrics is not implemented\']})",
        "p1d1eth1: (501, {\'errors\': [\'get_states is not implemented\']})",
        "p1d2eth1: (501, {\'errors\': [\'get_states is not implemented\']})"
    ]

    for res in responses:
        assert res.HasField('error')
        assert res.error.message in expected_error_msg

    change_mockserver_status(200, False)


@pytest.mark.asyncio
async def test_gnmi_server_set_api(snappiserver,
                                   gnmi_server):
    gnmi_api = init_gnmi_with_mock_server(200)

    found_err = False
    expected_err = 'Method not implemented!'
    try:
        await set(gnmi_api)
    except Exception as e:
        assert str(e) == expected_err
        found_err = True

    assert found_err, 'Exception should be raised'


@pytest.mark.asyncio
async def test_gnmi_server_get_api(snappiserver,
                                   gnmi_server):
    gnmi_api = init_gnmi_with_mock_server(200)

    found_err = False
    expected_err = 'Method not implemented!'
    try:
        await get(gnmi_api)
    except Exception as e:
        assert str(e) == expected_err
        found_err = True

    assert found_err, 'Exception should be raised'
