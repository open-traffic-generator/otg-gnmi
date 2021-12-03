from tests.utils.common import change_mockserver_status, create_new_session, crate_new_gnmi_server, kill_gnmi_server # noqa


def test_capabilites(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.capabilites()
        assert(result is True)
    finally:
        kill_gnmi_server(gnmi_server)


def test_get(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.get()
        assert(result is False)
    finally:
        kill_gnmi_server(gnmi_server)


def test_set(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.set()
        assert(result is False)
    finally:
        kill_gnmi_server(gnmi_server)


def test_subscribe_port_metrics(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.subscribe(['port_metrics'])
        assert(result is True)
    finally:
        kill_gnmi_server(gnmi_server)


def test_subscribe_flow_metrics(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.subscribe(['flow_metrics'])
        assert(result is True)
    finally:
        kill_gnmi_server(gnmi_server)


def test_subscribe_flow_bgpv4_metrics(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.subscribe(['bgpv4_metrics'])
        assert(result is True)
    finally:
        kill_gnmi_server(gnmi_server)


def test_subscribe_bgpv6_metrics(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.subscribe(['bgpv6_metrics'])
        assert(result is True)
    finally:
        kill_gnmi_server(gnmi_server)


def test_subscribe_isis_metrics(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.subscribe(['isis_metrics'])
        assert(result is True)
    finally:
        kill_gnmi_server(gnmi_server)


def test_subscribe_ipv4_neighbors_states(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.subscribe(['ipv4_neighbors'])
        assert(result is True)
    finally:
        kill_gnmi_server(gnmi_server)


def test_subscribe_ipv6_neighbors_states(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.subscribe(['ipv6_neighbors'])
        assert(result is True)
    finally:
        kill_gnmi_server(gnmi_server)


def test_subscribe_all(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
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
    finally:
        kill_gnmi_server(gnmi_server)


def test_subscribe_port_and_flow(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.subscribe(['port_metrics', 'flow_metrics'])
        assert(result is True)
    finally:
        kill_gnmi_server(gnmi_server)


def test_subscribe_port_and_protocol(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.subscribe(['port_metrics', 'bgpv4_metrics'])
        assert(result is True)
    finally:
        kill_gnmi_server(gnmi_server)


def test_subscribe_flow_and_protocol(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.subscribe(['flow_metrics', 'bgpv4_metrics'])
        assert(result is True)
    finally:
        kill_gnmi_server(gnmi_server)


def test_subscribe_multiple_protocol(snappiserver):
    gnmi_server = crate_new_gnmi_server()
    try:
        session = create_new_session()
        change_mockserver_status(200, False)
        result = session.subscribe(
            [
                'bgpv4_metrics',
                'bgpv6_metrics',
                'isis_metrics'
            ]
        )
        assert(result is True)
    finally:
        kill_gnmi_server(gnmi_server)
