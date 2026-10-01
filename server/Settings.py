#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json

def log(msg):
    pass

try:
    import sublime
except Exception as e:
    log(e)


def read_sublime_settings(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sublime.decode_value(f.read())
    except (IOError, ValueError):
        return None


class Settings(dict):

    def __init__(self):
        try:
            log('---- SETTING -------')
            cdir = os.path.dirname(os.path.abspath(__file__))
            if not "LiveReload" in cdir:
                cdir = os.path.join(sublime.packages_path(), 'LiveReload')
            self.file_name = os.path.join(cdir, '..', 'LiveReload.sublime-settings')
            data = read_sublime_settings(self.file_name) or {}

            # Merging user settings
            self.user_file_name = os.path.join(cdir, '..', '..', 'User', 'LiveReload.sublime-settings')
            data_user = read_sublime_settings(self.user_file_name) or {}

            for i in data:
                self[i] = data[i]

            for i in data_user:
                log(i)
                self[i] = data_user[i]
            log('LiveReload: Settings loaded')
            log('-----------')
        except Exception as e:
            log(e)

    def save(self):
        file_object = open(self.file_name, 'w')
        json.dump(self, file_object, indent=5)
        file_object.close()
        log('LiveReload: Settings saved')

    def get(self, key, default=None):
        try:
            return self[key]
        except Exception:
            return default

    def set(self, key, value):
        self[key] = value
        # persist only the changed key, in User file, leaving package defaults intact
        data_user = read_sublime_settings(self.user_file_name) or {}
        data_user[key] = value
        with open(self.user_file_name, 'w', encoding='utf-8') as f:
            json.dump(data_user, f, indent=4)

    def reload(self):
        self.__init__(self.file_name)
