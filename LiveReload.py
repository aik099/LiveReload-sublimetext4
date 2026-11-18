#!/usr/bin/python
# -*- coding: utf-8 -*-

# Starts and stops the server. Nothing imports this module: ST loads each root-level file as an independent plug-in,
# so shared code lives in the server subpackage (plug-ins use server.core).

import sys

from .server import core


def plugin_loaded():
    core.start()


def plugin_unloaded():
    core.stop()

    # ST and Package Control keep subpackage modules cached across unloads; drop them, so that a package upgrade
    # loads the new version's code
    package = core.__name__.rpartition('.')[0]
    for name in [n for n in sys.modules if n == package or n.startswith(package + '.')]:
        del sys.modules[name]
