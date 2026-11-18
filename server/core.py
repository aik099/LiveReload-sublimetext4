#!/usr/bin/python
# -*- coding: utf-8 -*-

import sublime
import os
import sys
import threading
import atexit
import time

from .WebSocketServer import WebSocketServer
from .SimpleResourceServer import SimpleResourceServer
from .SimpleCallbackServer import SimpleCallbackServer
from .SimpleWSServer import SimpleWSServer
from .LiveReloadAPI import LiveReloadAPI
from .PluginAPI import PluginInterface as Plugin
from .Settings import Settings


def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


class LiveReload(threading.Thread, SimpleCallbackServer,
    SimpleWSServer, SimpleResourceServer, LiveReloadAPI):

    """
    Start the LiveReload, which exposes public api.
    """

    def __init__(self):

        threading.Thread.__init__(self)
        SimpleCallbackServer.__init__(self)
        SimpleWSServer.__init__(self)
        SimpleResourceServer.__init__(self)
        LiveReloadAPI.__init__(self)

    def bind(self):
        """
        Bind the server port.
        """

        path = os.path.join(sublime.packages_path(), 'LiveReload', 'web'
                            , 'dist', 'livereloadjs-sm2.js')
        local = open(path, 'r')
        self.add_static_file('/livereload.js', local.read(),
                             'text/javascript')

        settings = Settings()
        self.port = settings.get('port', 35729)
        self.version = settings.get('version', '2.0')

        try:
            self.start_server(self.port)
        except Exception:
            # no error_message(): the dialog is modal for the whole app, and one hidden behind other windows
            # looks like a frozen Sublime Text
            message = 'LiveReload: port %d is busy, using %d' % (self.port, self.port + 1)
            print(message)
            sublime.status_message(message)
            self.start_server(self.port + 1)

    def start_server(self, port):
        """
        Bind the server.
        """

        self.ws_server = WebSocketServer(port, self.version)

    def run(self):
        """
        Serve requests until stopped.
        """

        self.ws_server.start()

    @atexit.register
    def clean(self):
        """
        Stop the server.
        """

        self.ws_server.stop()


# created on import, since plug-ins register callbacks on it while loading; serves after start()
API = LiveReload()


def start():
    """
    Bind the port, then serve in the background thread; bound first, so stop() never meets a server that isn't serving.
    """

    API.bind()
    API.start()


def stop():
    """
    Stop serving, close the port and disconnect browsers.
    """

    server = getattr(API, 'ws_server', None)
    if server:
        server.stop()


def http_callback(callback_f):
    """
    Add http callback to plugin defined function. For example request to GET /callback/plugin_name/log_me
    would trigger log_me function in plugin

    Example:
    ::

        @LiveReload.http_callback
        def compiled(self, req):
            print req # urlparse object
            return "cool" #to http client

    """

    callback_f.path = 'http://localhost:35729/callback/%s/%s' \
        % (callback_f.__module__.lower(), callback_f.__name__)
    API.callbacks.append({'path': callback_f.path,
            'name': callback_f.__name__, 'cls': callback_f.__module__})
    return callback_f


def websocket_callback(callback_f):
    """
    Add websocket callback to plugin defined function. For example on function call in browser
    LiveReload.SM2.plugin_name.definedfunction(data) would trigger definedfunction function in plugin or vice verse.
    Shortly you can call client functions from the server and server functions from client. Everything is JSON encoded
    by default.

    Example:
    ::

        @LiveReload.websocket_callback
        def compiled(self, json):
            print json # json object
            return "cool" #to http client {msg: "cool"}

    """

    callback_f.path = 'SM2.%s.%s' % (callback_f.__module__.lower(),
            callback_f.__name__)
    API.ws_callbacks.append({'path': callback_f.path,
            'name': callback_f.__name__, 'cls': callback_f.__module__})
    return callback_f
