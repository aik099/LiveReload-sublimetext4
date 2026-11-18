#!/usr/bin/python
# -*- coding: utf-8 -*-

import sublime
import os
import sys
import threading
import atexit
import time

try:

    # Python 3

    from .server.WebSocketServer import WebSocketServer
    from .server.SimpleResourceServer import SimpleResourceServer
    from .server.SimpleCallbackServer import SimpleCallbackServer
    from .server.SimpleWSServer import SimpleWSServer
    from .server.LiveReloadAPI import LiveReloadAPI
    from .server.PluginAPI import PluginInterface as Plugin
    from .server.Settings import Settings
except ValueError:

    # Python 2

    from server.WebSocketServer import WebSocketServer
    from server.SimpleResourceServer import SimpleResourceServer
    from server.SimpleCallbackServer import SimpleCallbackServer
    from server.SimpleWSServer import SimpleWSServer
    from server.LiveReloadAPI import LiveReloadAPI
    from server.PluginAPI import PluginInterface as Plugin
    from server.Settings import Settings


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
        Bind the server port; done before start(), so stop() never meets a server that isn't serving yet
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
            sublime.error_message('Port(' + str(self.port)
                                  + ') is already using, trying ('
                                  + str(self.port + 1) + ')')
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


if sublime.platform != 'build':
    try:
        API  # kept when ST reloads this module in place
    except NameError:
        API = LiveReload()
        API.bind()
        API.start()


def plugin_unloaded():
    """
    Stop the server when ST unloads or reloads this module (e.g. a package upgrade), so the next load can bind the port.
    """

    global API
    try:
        server = API
    except NameError:
        return
    del API
    server.ws_server.stop()


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
