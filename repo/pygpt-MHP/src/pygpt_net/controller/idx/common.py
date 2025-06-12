#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2024.12.16 01:00:00                  #
# ================================================== #

from typing import List, Dict


class Common:
    def __init__(self, window=None):
        """
        Idx common controller

        :param window: Window instance
        """
        self.window = window

    def setup(self):
        """Set up UI"""
        checkbox = None
        try:
            checkbox = self.window.ui.config['global']['llama.idx.raw']
        except Exception:
            checkbox = None
        if checkbox is not None:
            value = self.window.core.config.get('llama.idx.raw', False)
            checkbox.setChecked(value)

    def toggle_raw(self, value: bool):
        """Toggle raw query mode"""
        self.window.core.config.set('llama.idx.raw', value)
        self.window.core.config.save()

    def get_loaders_choices(self) -> List[Dict[str, str]]:
        """
        Get available loaders choices

        Prefixes:
            file_ - file loader
            web_ - web loader
            online_ - online loader

        :return: list of available loaders
        """
        data = []

        # offline (built-in)
        loaders = self.window.core.idx.indexing.get_data_providers()
        for id in loaders:
            loader = loaders[id]
            # file
            if "file" in loader.type:
                id = "file_" + id
                ext_str = ""
                if loader.extensions:
                    ext_str = " (" + ", ".join(loader.extensions) + ")"
                # name = "(File) " + loader.name + ext_str  # TODO: implement option names
                data.append({
                    id: loader.name
                })
                # sort by name
                data = sorted(data, key=lambda x: list(x.values())[0])
            # web
            if "web" in loader.type:
                id = "web_" + id
                # name = "(Web) " + loader.name  # TODO: implement option names
                data.append({
                    id: loader.name
                })
                # sort by name
                data = sorted(data, key=lambda x: list(x.values())[0])
        return data
