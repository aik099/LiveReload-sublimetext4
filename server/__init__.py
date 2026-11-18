#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys


def live_reload():
    """The core module (API, Plugin); looked up at call time, since core imports the modules that call this"""
    return sys.modules[__name__ + '.core']
