# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

LiveReload package for Sublime Text 3 and 4. It is published on Package Control as `LiveReload`, with releases taken from semver git tags. This fork (aik099) succeeds the archived alepez repo; see the README "History" section.

## Runtime constraints

- The code must run on all of ST's plugin hosts: Python 3.3, 3.8 and 3.14. Don't use f-strings, `pathlib` niceties or APIs added after Python 3.3. Also avoid APIs removed in Python 3.9 or later (`'rU'`, `base64.encodestring`, `array.fromstring/tostring`).
- There is no `.python-version` on purpose. ST picks the 3.3 host where it is enabled, else the newest host.
- `.no-sublime-package` keeps the package unzipped: `server/core.py` reads `web/dist/livereloadjs-sm2.js` from disk.
- Use only the basic, ST3-era `sublime` API.

## Architecture

- **No root `__init__.py`:** Package Control 4 drops it on install, so the package must work without one. ST imports each top-level `.py` as `LiveReload.<name>`, as an independent plug-in.
- **No imports between root-level files:** the channel's reviewer (`kaste/st_package_reviewer`) fails a package for it. Shared code lives in the `server` subpackage.
- **Server object:** `server/core.py` creates the server object `API` on import, without binding the port, because plug-ins register HTTP / websocket callbacks on it while they load. It also exports `Plugin`, `http_callback` and `websocket_callback`. `API` is one class mixing in `SimpleCallbackServer`, `SimpleWSServer`, `SimpleResourceServer` and `LiveReloadAPI`. It is a hand-written websocket and HTTP server in `server/WebSocketServer.py`, `WebSocketClient.py` and `WSRequestHandler.py`. On the same port it serves `/livereload.js`, plug-in static files, `/callback/<module>/<func>` HTTP callbacks and the websocket. If the port is busy, it falls back to port+1.
- **Server lifecycle** (root `LiveReload.py`, imported by nothing):
  - `plugin_loaded()` calls `core.start()`, which binds the port and then serves in a thread. The port is bound before the thread serves, because `socketserver`'s `shutdown()` deadlocks on a server that never serves.
  - `plugin_unloaded()` calls `core.stop()`, which stops serving, closes the port and disconnects browsers. It then drops `LiveReload.server*` from `sys.modules`, because neither ST nor Package Control clears a package's submodules, and an upgrade would otherwise run the old server code.
- **Plug-in loading:** each top-level `*Plugin.py` / `*Callback.py` does `from .server import core as LiveReload` and subclasses `LiveReload.Plugin` together with `sublime_plugin.EventListener`. `server/*` modules get `core` via `server.live_reload()` at call time, because `core` imports them while it is still loading.
- **Plug-in registry:** the `PluginFactory` metaclass in `server/PluginAPI.py` registers plug-ins by class name. `name` = class name, and enabled plug-ins are stored as class names in `enabled_plugins`. `refresh()` / `sendCommand()` send a LiveReload-protocol `reload` command to every websocket client. `file_types` filtering lets a specific plug-in take a file instead of a `*` plug-in.
- **Settings:** `server/Settings.py` merges the package `LiveReload.sublime-settings` with `Packages/User/LiveReload.sublime-settings`, located via `sublime.packages_path()` because the package dir may be a symlink. `set()` writes only the changed key to the User file. The package defaults file must never be written.
- **Commands:** `CommandAPI.py` holds the `ApplicationCommand`s used by `Main.sublime-menu` and `Default.sublime-commands`.
- **Browser client:** `web/` is the client. `web/dist/*.js` is committed and is what gets served. `web/src/*.coffee` plus the Grunt build are 2013-era tooling and are not run.
- **Package Control messages:** `messages.json` uses the keys `install` and `<version>`. Add a `messages/<version>.txt` only for releases worth an upgrade notice.
- **Download contents:** `.gitattributes` `export-ignore` keeps dev-only files out of Package Control downloads. Add new dev-only files there.

## Development

- **Smoke test:** `tests/smoke.sh <python version>` (e.g. `3.3`, `3.8`, `3.14`; needs Docker). It loads the package as Package Control downloads it (`git archive`, including uncommitted changes to tracked files) with stubbed `sublime` / `sublime_plugin` modules (`tests/stubs/`). It checks that:
  - plug-ins load and `livereload.js` is served;
  - a save sends a reload over the websocket;
  - a plug-in reload keeps working;
  - an unload and reload of the whole package (an upgrade) restarts the server on fresh code.

  New files must be staged (`git add`) before the test sees them.
- **CI** (`.github/workflows/ci.yml`):
  - the smoke test on 3.3, 3.8 and 3.14;
  - `python3.14 -W error -m compileall` (invalid escapes and other syntax warnings);
  - `kaste/st_package_reviewer` (the reviewer the Package Control channel runs) on the `git archive` export.
- `web/test.html` ("LiveReload: Self test") is broken (issue #2).
- **Manual test:** symlink this repo as `Packages/LiveReload`, enable "Simple Reload" via "LiveReload: Enable/disable plug-ins" and open a page that loads `http://localhost:<port>/livereload.js`. Saving a file should reload the page.
- **Restarts:**
  - After editing `server/*` or the root `LiveReload.py`, restart Sublime Text. Submodules are not hot-reloaded, and a hot reload of `LiveReload.py` restarts the server on fresh code that the already loaded plug-ins don't use.
  - Plug-in files hot-reload fine.
  - With the symlinked clone, every edit hits the running ST.
- **Releases:**
  - Create a signed annotated tag (`git tag -s X.Y.Z`) on `master`, then a GitHub release.
  - Tag only after the maintainer has reviewed and tested the change in ST.
  - Tags `0.1.x`/`0.2.0` are historical and unsigned.
