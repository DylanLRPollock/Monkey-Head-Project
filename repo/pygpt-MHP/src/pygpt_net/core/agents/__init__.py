#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/core/agents

# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2024.11.17 03:00:00                  #
# ================================================== #

from .legacy import Legacy
from .memory import Memory
from .observer import Observer
from .provider import Provider
from .runner import Runner
from .tools import Tools


class Agents:
    def __init__(self, window=None):
        """
        Agents core

        :param window: Window instance
        """
        self.window = window
        self.legacy = Legacy(window)
        self.memory = Memory(window)
        self.observer = Observer(window)
        self.provider = Provider(window)
        self.runner = Runner(window)
        self.tools = Tools(window)
