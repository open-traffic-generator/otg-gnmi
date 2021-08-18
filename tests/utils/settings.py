import json
import os
import sys

if sys.version_info[0] >= 3:
    # alias str as unicode for python3 and above
    unicode = str


def get_root_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dict_items(d):
    try:
        # python 3
        return d.items()
    except Exception:
        # python 2
        return d.iteritems()


def object_dict_items(ob):
    return dict_items(ob.__dict__)


def byteify(val):
    if isinstance(val, dict):
        return {byteify(key): byteify(value) for key, value in dict_items(val)}
    elif isinstance(val, list):
        return [byteify(element) for element in val]
    # change u'string' to 'string' only for python2
    elif isinstance(val, unicode) and sys.version_info[0] == 2:
        return val.encode('utf-8')
    else:
        return val


def load_dict_from_json_file(path):
    """
    Safely load dictionary from JSON file in both python2 and python3
    """
    with open(path, 'r') as fp:
        return json.load(fp, object_hook=byteify)


# path to gnmi_settings.json and gnmi_test_settings.json relative root dir
GNMI_SETTINGS_FILE = 'gnmi_settings.json'
GNMI_TEST_CONFIG_FILE = 'gnmi_test_config.json'


class BaseSettings(object):
    def __init__(self, settings_file):
        self.setings_file = settings_file

    def load_from_settings_file(self):
        self.__dict__ = load_dict_from_json_file(self.get_settings_path())

    def get_settings_path(self):
        return os.path.join(get_root_dir(), self.setings_file)

    def load_from_pytest_command_line(self, config):
        for key, val in object_dict_items(self):
            new_val = config.getoption(key)
            if new_val is not None:
                if key in ['license_servers', 'ports']:
                    # items in a list are expected to be passed in as a string
                    # where each item is separated by whitespace
                    setattr(self, key, new_val.split())
                else:
                    setattr(self, key, new_val)

    def register_pytest_command_line_options(self, parser):
        for key, val in object_dict_items(self):
            parser.addoption("--%s" % key, action="store", default=None)

    def to_string(self):
        return self.__dict__

    def serialize(self):
        print('Serialize: %s' % json.dumps(self.__dict__))
        return json.dumps(self.__dict__)


class GnmiSettings(BaseSettings):
    """
    Singleton for global settings
    """
    def __init__(self):
        # these not be defined and are here only for documentation
        super().__init__(GNMI_SETTINGS_FILE)
        self.quiet = None
        self.verbose = None
        self.server = None
        self.username = None
        self.password = None
        self.cert = None
        self.tls = None
        self.altName = None
        self.ciphers = None
        self.interval = None
        self.timeout = None
        self.heartbeat = None
        self.aggregate = None
        self.suppress = None
        self.submode = None
        self.mode = None
        self.paths = None
        self.prefix = None
        self.qos = None
        self.use_alias = None
        self.stats = None
        self.waitForResponses = None
        self.load_from_settings_file()
        self.authentication = [self.username, self.password]
        self.metadata = [
            ('username', self.username),
            ('password', self.password)
        ]

    def is_done(self, curr_upds):
        if self.waitForResponses != 0 and self.waitForResponses <= curr_upds:
            return True
        return False


class GnmiTestConfig(BaseSettings):
    """
    Singleton for global test config
    """
    def __init__(self):
        # these not be defined and are here only for documentation
        super().__init__(GNMI_TEST_CONFIG_FILE)
        self.ports = None
        self.flows = None
        self.load_from_settings_file()


if __name__ == '__main__':
    # shared global settings
    gnmiSettings = GnmiSettings()
    print(gnmiSettings.__dict__)

    gnmiTestConfig = GnmiTestConfig()
    print(gnmiTestConfig.__dict__)
