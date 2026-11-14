#!/usr/bin/python
# -*- coding: utf-8 -*-

import sublime
import sublime_plugin
import LiveReload
import webbrowser
import os

try:
    from .server.PluginAPI import PluginInterface as Plugin
except ValueError:
    from server.PluginAPI import PluginInterface as Plugin


class LiveReloadTest(sublime_plugin.ApplicationCommand):

    def run(self):
        path = os.path.join(sublime.packages_path(), 'LiveReload', 'web')
        file_name = os.path.join(path, 'test.html')
        webbrowser.open_new_tab("file://"+file_name)


class LiveReloadHelp(sublime_plugin.ApplicationCommand):

    def run(self):
        webbrowser.open_new_tab('https://github.com/aik099/LiveReload-sublimetext4#using'
                                )


class LiveReloadEnablePluginCommand(sublime_plugin.ApplicationCommand):

    def on_done(self, index):
        if index != -1:
            Plugin.togglePlugin(index)

    def run(self):
        sublime.active_window().show_quick_panel(Plugin.listPlugins(),
                self.on_done)
