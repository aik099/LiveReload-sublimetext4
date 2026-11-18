#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import sublime
import sublime_plugin

from . import LiveReload

##Modlue name must be the same as class or else callbacks won't work
class SimpleReloadCallback(LiveReload.Plugin):

    title = 'Simple Reload from http GET request'
    description = \
        'Refresh page, on http://localhost:35729/callback/simplereloadplugincallback/on_post_compile'
    file_types = '*'
    this_session_only = True

    @LiveReload.http_callback
    def on_post_compile(self, req):
        self.refresh(os.path.basename(sublime.active_window().active_view().file_name()))
        return 'All ok from SimpleRefreshCallBack!'
