from tests.utils.common import change_mockserver_status


def test_capabilites(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.capabilites()
    assert(result is True)


def test_get(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.get()
    assert(result is False)


def test_set(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.set()
    assert(result is False)


def test_subscribe_port_metrics(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.subscribe(['port_metrics'])
    assert(result is True)


def test_subscribe_flow_metrics(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.subscribe(['flow_metrics'])
    assert(result is True)


def test_subscribe_flow_bgpv4_metrics(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.subscribe(['bgpv4_metrics'])
    assert(result is True)


def test_subscribe_bgpv6_metrics(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.subscribe(['bgpv6_metrics'])
    assert(result is True)


def test_subscribe_isis_metrics(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.subscribe(['isis_metrics'])
    assert(result is True)


def test_subscribe_all(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.subscribe(
        [
            'port_metrics',
            'flow_metrics',
            'bgpv4_metrics',
            'bgpv6_metrics',
            'isis_metrics'
        ]
    )
    assert(result is True)


def test_subscribe_port_and_flow(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.subscribe(['port_metrics', 'flow_metrics'])
    assert(result is True)


def test_subscribe_port_and_protocol(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.subscribe(['port_metrics', 'bgpv4_metrics'])
    assert(result is True)


def test_subscribe_flow_and_protocol(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.subscribe(['flow_metrics', 'bgpv4_metrics'])
    assert(result is True)


def test_subscribe_multiple_protocol(gnmi_server, snappiserver, session):
    change_mockserver_status(200, False)
    result = session.subscribe(
        [
            'bgpv4_metrics',
            'bgpv6_metrics',
            'isis_metrics'
        ]
    )
    assert(result is True)
