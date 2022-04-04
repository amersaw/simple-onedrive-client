# Import server module

import http.server
import socketserver


# Import SocketServer module
def GetPythonServer(stopping_path):
    class PythonServer(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith(stopping_path):
                self.server.stoppingValue = self.path
                self.server.stopped = True

    return PythonServer


class CallbackHttpListner(socketserver.TCPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stopped = False
        self.stoppingValue = None

    def run_till_stopped(self):
        while self.stopped == False:
            self.handle_request()

        return self.stoppingValue

    @staticmethod
    def listen_till_callback_received(
        *, host="", port=7700, stopping_path="/callback"
    ) -> str:
        server = CallbackHttpListner(("", port), GetPythonServer(stopping_path))
        return server.run_till_stopped()
