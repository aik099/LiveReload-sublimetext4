#!/usr/bin/python
# -*- coding: utf-8 -*-
try:
    from SimpleHTTPServer import SimpleHTTPRequestHandler
except ImportError:
    from http.server import SimpleHTTPRequestHandler

from . import live_reload

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import os
import sys

# HTTP handler with WebSocket upgrade support

class WSRequestHandler(SimpleHTTPRequestHandler):

    def __init__(
        self,
        req,
        addr,
        ):

        # Python 3.7+ calls os.getcwd() without `directory`, failing if plugin_host's cwd was deleted
        kwargs = {'directory': os.path.dirname(os.path.abspath(__file__))} if sys.version_info >= (3, 7) else {}
        SimpleHTTPRequestHandler.__init__(self, req, addr, object(), **kwargs)

        self.server_version = 'LiveReload/1.0'

    def do_GET(self):
        if self.headers.get('upgrade') and self.headers.get('upgrade').lower() == 'websocket':

            if self.headers.get('sec-websocket-key1') or self.headers.get('websocket-key1'):

                # For Hixie-76 read out the key hash

                self.headers.__setitem__('key3', self.rfile.read(8))

            # Just indicate that an WebSocket upgrade is needed

            self.last_code = 101
            self.last_message = '101 Switching Protocols'
        else:
            req = urlparse(self.path)
            _file = live_reload().API.has_file(req.path)
            _httpcallback = live_reload().API.has_callback(req.path)
            if _httpcallback:
                try:
                    plugin = live_reload().Plugin.getPlugin(_httpcallback['cls'])
                    func = getattr(plugin, _httpcallback['name'], None)
                    if func:
                        res = func(req)
                        self.send_response(200, res)
                    else:
                        res = "Callback method not found"
                        self.send_response(404, 'Not Found')
                except Exception as e:
                    self.send_response(500, 'Error')
                    res = e
                
                self.send_header('Content-type', 'text/plain')
                self.send_header('Content-Length', len(res))
                self.end_headers()
                self.wfile.write(bytes(res.encode("UTF-8")))
                return
            elif _file:
                if hasattr(_file['buffer'], 'read'):
                    _buffer = _file['buffer'].read()
                else:
                    _buffer = _file['buffer']

                self.send_response(200, 'OK')
                self.send_header('Content-type', _file['content_type'])
                self.send_header('Content-Length', len(_buffer))
                self.end_headers()
                self.wfile.write(bytes(_buffer.encode("UTF-8")))
                return
            else:

                # Disable other requests
                notallowed = "Method not allowed"
                
                self.send_response(405, notallowed)
                self.send_header('Content-type', 'text/plain')
                self.send_header('Content-Length', len(notallowed))
                self.end_headers()
                self.wfile.write(bytes(notallowed.encode("utf-8")))
                return

    def send_response(self, code, message=None):

        # Save the status code

        self.last_code = code
        SimpleHTTPRequestHandler.send_response(self, code, message)

    def log_message(self, f, *args):

        # Save instead of printing

        self.last_message = f % args
