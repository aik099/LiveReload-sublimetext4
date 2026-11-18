#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import sublime
import sublime_plugin

from .server import core as LiveReload

##Modlue name must be the same as class or else callbacks won't work
class SimpleWSCallback(LiveReload.Plugin, sublime_plugin.EventListener):

    title = 'Send content on change'
    description = \
        'Send file content to browser console'
    file_types = '*'
    this_session_only = True

    def on_modified_async(self, view):
      if self.isEnabled:
        region = sublime.Region(0, view.size())
        source = view.substr(region)
        self.sendRaw("socket", source)
        
    def onReceive(self, data, origin):
      print(data)
