# Smoke test: loads the package like ST does (Packages/LiveReload without a root __init__.py, each top-level module
# imported as LiveReload.<name>, then plugin_loaded()), then checks the server, a plug-in, a plug-in reload, and an
# unload and load of the whole package (upgrade).
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


def http_get(path, port=PORT):
    s = socket.create_connection(('127.0.0.1', port), 5)
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


plugin_names = sorted('LiveReload.' + f[:-3] for f in os.listdir(pkg_dir) if f.endswith('.py'))


def load_package():
    # ST imports root-level files in name order, then calls their plugin_loaded() once all are loaded
    for name in plugin_names:
        importlib.import_module(name)
    for name in plugin_names:
        hook = getattr(sys.modules[name], 'plugin_loaded', None)
        if hook:
            hook()
    time.sleep(0.5)
    return sys.modules['LiveReload.server.core']


def unload_package():
    # package upgrade or disabling: plugin_unloaded(), then the module is dropped
    for name in plugin_names:
        hook = getattr(sys.modules[name], 'plugin_unloaded', None)
        if hook:
            hook()
        del sys.modules[name]


core = load_package()
check(b' 200 ' in http_get('/livereload.js').split(b'\r\n')[0], 'livereload.js served')
Plugin = core.Plugin
names = [p.__name__ for p in Plugin.plugins]
check(len(names) == 8, 'all plug-ins registered: ' + ', '.join(names))
Plugin.togglePlugin(names.index('SimpleRefresh'))
with open(os.path.join(packages, 'User', 'LiveReload.sublime-settings')) as f:
    check('SimpleRefresh' in f.read(), 'enabled plug-in saved to User settings')
ws = ws_connect()
save_reloads(ws, 'first load')

# ST reloading a changed plug-in in place: its class replaces the old one, the server keeps running
reload(sys.modules['LiveReload.SimpleReloadPlugin'])
save_reloads(ws, 'after plug-in reload')

unload_package()
check(ws.recv(65536) == b'', 'browser socket closed on unload')
check(not [n for n in sys.modules if n.startswith('LiveReload.server')], 'server modules dropped on unload')
new_core = load_package()
check(new_core is not core, 'reload after unload runs fresh server code')
ws = ws_connect()
save_reloads(ws, 'after unload and load (upgrade), enabled plug-in remembered')

check(sublime.errors == [], 'no error dialogs')

# busy port: the fallback port serves, reported without a modal dialog (one hidden behind windows froze ST)
unload_package()
blocker = socket.socket()
blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
blocker.bind(('', PORT))
blocker.listen(1)
core = load_package()
check(b' 200 ' in http_get('/livereload.js', PORT + 1).split(b'\r\n')[0], 'busy port: fallback port serves')
check(sublime.errors == [], 'busy port: no modal dialog')
check([m for m in sublime.statuses if 'busy' in m], 'busy port: reported in the status bar')
unload_package()
blocker.close()

print('SMOKE OK on Python ' + sys.version.split()[0])
sys.stdout.flush()
os._exit(0)
