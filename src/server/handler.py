from http.server import BaseHTTPRequestHandler
import os
from src.utils import result
import urllib.parse as parse
import sys
from importlib import import_module


def grand(sv, path, data):
    p = "public/html" + path
    if os.path.exists(p):
        with open(p, "rb") as obj:
            sv.send_response(200)
            sv.end_headers()
            sv.wfile.write(obj.read())
        return True
    return False


def text(path, replaces):
    with open("public/html" + path, "r", encoding="utf-8") as r:
        txt = r.read()
    for replace in replaces:
        txt = txt.replace("%%" + replace[0] + "%%", replace[1])
    return


def write(sv, code, txt):
    sv.send_response(code)
    sv.send_header("Content-Type", "application/json")
    sv.end_headers()
    sv.wfile.write(txt.encode())


class Handler(BaseHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        self.logger = server.logger
        self.token = server.token
        self.instance = server.instance
        self.config = self.instance.config
        super().__init__(request, client_address, server)

    def log_message(self, format, *args):
        self.logger.info("server", self.address_string() + " -> " + format % args)

    def do_GET(self):
        if "Authorization" not in self.headers:
            result.qe(self, result.Cause.AUTH_REQUIRED)
            return
        try:
            path = parse.urlparse(self.path)
            params = parse.parse_qs(path.query)

            auth = self.headers["Authorization"].split(" ")
            if len(auth) is not 2:
                result.qe(self, result.Cause.AUTH_REQUIRED)
                return
            if str(auth[0]).lower() != "token":
                result.qe(self, result.Cause.AUTH_REQUIRED)
                return
            if not self.token.validate(auth[1]):
                result.qe(self, result.Cause.AUTH_REQUIRED)
                return

            self.handleRequest(path, params)
        except Exception as e:
            tb = sys.exc_info()[2]
            self.logger.severe("instance",
                               "An error has occurred while processing request from client: {0}"
                               .format(e.with_traceback(tb)))

    def handleRequest(self, path, params):
        try:
            handler = import_module("src.server.handler_root" + path.path.replace("/", "."))
            handler.handle(self, path, params)
        except ModuleNotFoundError:
            result.qe(self, result.Cause.EP_NOTFOUND)
