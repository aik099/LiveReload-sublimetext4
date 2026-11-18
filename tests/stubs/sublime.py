# Minimal stand-in for ST's sublime module, enough for tests/smoke.py
import json
import os

PACKAGES = os.environ['ST_PACKAGES']
errors = []
statuses = []


def packages_path():
    return PACKAGES


def platform():
    return 'linux'


def decode_value(s):
    return json.loads(s)


def set_timeout(f, ms=0):
    f()


def status_message(msg):
    print('STATUS: ' + msg)
    statuses.append(msg)


def error_message(msg):
    # modal for the whole ST app until answered
    print('ERROR DIALOG: ' + msg)
    errors.append(msg)


def load_settings(name):
    return {}
