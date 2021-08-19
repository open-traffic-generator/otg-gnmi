
# client_session.py


class ClientSession(object):
    def __init__(self, context, requests):
        self.context = context
        self.subscribed_paths = {}
        self.sent_sync = False
        self.mode = 0  # STREAM=0, ONCE=1, POLL=2
        self.requests = requests

    def send_sync(self):
        if self.sent_sync is False:
            for val in self.subscribed_paths.values():
                if val == 0:
                    return False
            self.sent_sync = True
            return True
        else:
            return False

    def register_path(self, path):
        if path not in self.subscribed_paths:
            self.subscribed_paths[path] = 0

    def deregister_path(self, path):
        if path in self.subscribed_paths:
            self.subscribed_paths.pop(path)

    def update_stats(self, path):
        if path in self.subscribed_paths:
            self.subscribed_paths[path] += 1
