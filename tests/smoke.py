# Smoke test: loads the package like ST does (Packages/LiveReload without a root __init__.py, each top-level module
# imported as LiveReload.<name>), then checks the server, a plug-in, and ST's reload and unload of the main module.
# Run via tests/smoke.sh; Python 3.3 compatible.
import os
import sys
import time
import socket
import importlib
import traceback
try:
    from imp import reload
except ImportError:
    from importlib import reload

import sublime

PORT = 35729
packages = os.environ['ST_PACKAGES']
sys.path.insert(0, packages)
pkg_dir = os.path.join(packages, 'LiveReload')
assert not os.path.exists(os.path.join(pkg_dir, '__init__.py')), 'Package Control drops the root __init__.py'


def fail_fast(exc_type, exc, tb):
    # the server's non-daemon thread would otherwise keep the process alive
    traceback.print_exception(exc_type, exc, tb)
    sys.stdout.flush()
    os._exit(1)


sys.excepthook = fail_fast


def check(ok, msg):
    if not ok:
        print('FAIL: ' + msg)
        sys.stdout.flush()
        os._exit(1)
    print('ok: ' + msg)


def http_get(path):
    s = socket.create_connection(('127.0.0.1', PORT), 5)
    s.sendall(('GET ' + path + ' HTTP/1.0\r\nHost: localhost\r\n\r\n').encode())
    data = b''
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        data += chunk
    s.close()
    return data


def ws_connect():
    s = socket.create_connection(('127.0.0.1', PORT), 5)
    s.sendall(b'GET /livereload HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
              b'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n')
    check(b' 101 ' in s.recv(4096).split(b'\r\n')[0], 'websocket handshake')
    time.sleep(0.5)
    s.settimeout(3)
    return s


class View(object):
    def file_name(self):
        return '/tmp/page.html'


def save_reloads(ws, label):
    sys.modules['LiveReload.SimpleReloadPlugin'].SimpleRefresh().on_post_save(View())
    check(b'"reload"' in ws.recv(65536), label + ': save sends reload')


# ST imports plug-ins in name order; the first one imports LiveReload.LiveReload, which starts the server
for f in sorted(os.listdir(pkg_dir)):
    if f.endswith('.py'):
        importlib.import_module('LiveReload.' + f[:-3])
lr = sys.modules['LiveReload.LiveReload']
time.sleep(0.5)

check(b' 200 ' in http_get('/livereload.js').split(b'\r\n')[0], 'livereload.js served')
Plugin = lr.Plugin
names = [p.__name__ for p in Plugin.plugins]
check(len(names) == 8, 'all plug-ins registered: ' + ', '.join(names))
Plugin.togglePlugin(names.index('SimpleRefresh'))
with open(os.path.join(packages, 'User', 'LiveReload.sublime-settings')) as f:
    check('SimpleRefresh' in f.read(), 'enabled plug-in saved to User settings')
ws = ws_connect()
save_reloads(ws, 'first load')

# ST reloading a changed module in place: plugin_unloaded(), then reload with the module's globals kept
old_api = lr.API
lr.plugin_unloaded()
check(ws.recv(65536) == b'', 'browser socket closed on unload')
reload(lr)
time.sleep(0.5)
check(lr.API is not old_api, 'in-place reload started a new server')
ws = ws_connect()
save_reloads(ws, 'after in-place reload')

# full unload (package upgrade, disabling the package), then a fresh import
lr.plugin_unloaded()
del sys.modules['LiveReload.LiveReload']
lr = importlib.import_module('LiveReload.LiveReload')
time.sleep(0.5)
ws = ws_connect()
save_reloads(ws, 'after full unload')

check(sublime.errors == [], 'no error dialogs')
print('SMOKE OK on Python ' + sys.version.split()[0])
sys.stdout.flush()
os._exit(0)
