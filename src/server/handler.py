from http.server import BaseHTTPRequestHandler
import os
import route
import urllib.parse as parse
import sys
import threading
from importlib import import_module
import json
import mimetypes
import cgi
import traceback
import asyncio
import inspect

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

    def parse_thread_name(self, name):
        name = str.strip(name, "ThreadPoolExecutor-")
        splittext = str.split(name, "_")

        return f"thread-{splittext[0]}-{splittext[1]}"

    def getLogName(self):
        return self.parse_thread_name(threading.current_thread().getName())

    def log_message(self, format, *args):
        self.logger.info(self.getLogName(), self.address_string() +
                         " -> " + format % args)

    def do_auth(self):
        if "Authorization" not in self.headers:
            route.post_error(self, route.Cause.AUTH_REQUIRED)

            return True

        auth = self.headers["Authorization"].split(" ")

        if len(auth) != 2:
            route.post_error(self, route.Cause.AUTH_REQUIRED)

            return True

        if str(auth[0]).lower() != "token":
            route.post_error(self, route.Cause.AUTH_REQUIRED)

            return True

        if not self.token.validate(auth[1]):
            route.post_error(self, route.Cause.AUTH_REQUIRED)

            return True
        return False

    def do_GET(self):

        try:
            path = parse.urlparse(self.path)
            params = parse.parse_qs(path.query)

            if path.path == "/docs.html":
                self.handleRequest(path, params)

                return

            if self.do_auth():
                return

            for param in list(params.keys()):
                params[param] = params[param][0]

            self.handleRequest(path, params)
        except:
            self.printStacktrace(*sys.exc_info())

    def do_POST(self):
        try:
            if self.do_auth():
                return

            path = parse.urlparse(self.path)
            if "Content-Type" not in self.headers:
                route.post_error(self, route.Cause.NOT_ALLOWED_OPERATION)

                return

            contentType = self.headers["Content-Type"]

            if contentType == "application/x-www-form-urlencoded":
                contentLen = int(self.headers.get("content-length"))
                reqBody = self.rfile.read(contentLen).decode("utf-8")
                self.handleRequest(path, parse.parse_qs(reqBody))
                return
            elif contentType.startswith("multipart/form-data"):
                f = cgi.FieldStorage(fp=self.rfile,
                                     headers=self.headers,
                                     environ={
                                         "REQUEST_METHOD": "POST",
                                         "CONTENT_TYPE": contentType,
                                     },
                                     encoding="utf-8")
                if "file" not in f:
                    route.post_error(self, route.Cause.INVALID_FIELD_UNK)
                    return
                params = {}
                for fs in f.keys():
                    params[fs] = f.getvalue(fs)
                self.handleRequest(path, params)
        except:
            self.printStacktrace(*sys.exc_info())

    def handleRequest(self, path, params):

        if ".." in path.path:
            route.post_error(self, route.Cause.EP_NOTFOUND)

            return

        p = path.path.replace("/", ".")

        if p.endswith("."):
            p = p[:-1]

        try:
            handler = import_module("server.handler_root" + p)

            if inspect.iscoroutinefunction(handler.handle):
                asyncio.run(handler.handle(self, path, params))
            else:
                handler.handle(self, path, params)

        except (ModuleNotFoundError, AttributeError):
            try:
                handler = import_module("server.handler_root" + p + "._")

                if inspect.iscoroutinefunction(handler.handle):
                    asyncio.run(handler.handle(self, path, params))
                else:
                    handler.handle(self, path, params)
            except (ModuleNotFoundError, AttributeError):
                if os.path.exists("resources/handle" + path.path + ".txt"):
                    with open("resources/handle" + path.path + ".txt", encoding="utf-8", mode="r") as r:
                        content = r.read().split("\n")
                        route.success(self, int(content[0]), content[1:])
                        return
                if os.path.exists("resources/handle" + path.path + ".json"):
                    with open("resources/handle" + path.path + ".json", encoding="utf-8", mode="r") as r:
                        content = json.JSONDecoder().decode(r.read())
                        write(self, content["c"], json.JSONEncoder().encode(content["o"]))
                        return
                if os.path.exists("resources/resource" + path.path):
                    with open("resources/resource" + path.path, mode="rb") as r:
                        self.send_response(200)
                        self.send_header("Content-Type", mimetypes.guess_type("resources/resource" + path.path)[0])
                        self.end_headers()
                        self.wfile.write(r.read())
                        return
                route.post_error(self, route.Cause.EP_NOTFOUND)
        except Exception as e:
            self.printStacktrace(*sys.exc_info())
            pass

    def handle_one_request(self):
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                return
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(
                    400,
                    "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            method()
            if not self.wfile.closed:
                self.wfile.flush()
                self.wfile.close()
        except Exception as e:
            self.printStacktrace(*sys.exc_info())
            self.close_connection = True
            return

    def send_response(self, code, message=None):
        self.log_request(code)
        self.send_response_only(code, message)
        self.send_header("Server", "gws")
        self.send_header("Connection", "close")

    def printStacktrace(self, etype, exception, trace):
        tb = traceback.TracebackException(etype, exception, trace)

        st = f"Unexpected exception while handling client request resource {self.path}\n"

        flag = False

        for stack in tb.stack:
            stack: traceback.FrameSummary
            if "handler_root" in stack.filename and not flag:
                flag = True
                st = st + "Caused by: " + self.getClassChain(etype) + ": " + str(tb) + "\n"
            st = st + "        at " + self.normalizeFileName(stack.filename) + "." + stack.name \
                 + "(" + os.path.basename(stack.filename) + ":" + str(stack.lineno) \
                 + "): " + stack.line + "\n"

        self.logger.warn(self.parse_thread_name(threading.current_thread().getName()), st)

    @staticmethod
    def normalizeFileName(path: str):
        das = path.split("src")
        del das[0]
        da = "".join(das)
        da = da.replace("\\", ".").replace("/", ".")
        return da[1:-3]

    @staticmethod
    def getClassChain(clazz):
        mod = clazz.__module__
        if mod == "builtins":
            return clazz.__qualname__
        return f"{mod}.{clazz.__qualname__}"
