#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import sublime
import sublime_plugin

from . import LiveReload


class SimpleRefreshDelay(LiveReload.Plugin, sublime_plugin.EventListener):

    title = 'Simple Reload with delay(400ms)'
    description = 'Wait 400ms then refresh page, when file is saved'
    file_types = '*'

    def on_post_save(self, view):
        ref = self
        sublime.set_timeout(lambda : ref.refresh(os.path.basename(view.file_name())), 400)
