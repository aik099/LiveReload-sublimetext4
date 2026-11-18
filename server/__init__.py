#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys


def live_reload():
    """The package's LiveReload module (API, Plugin); looked up at call time, since it imports this package while loading"""
    return sys.modules[__name__.rpartition('.')[0] + '.LiveReload']
