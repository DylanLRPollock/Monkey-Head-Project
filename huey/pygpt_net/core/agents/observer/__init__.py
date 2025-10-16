#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey/pygpt_net/core/agents/observer

# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2024.11.17 03:00:00                  #
# ================================================== #

from .evaluation import Evaluation


class Observer:
    def __init__(self, window=None):
        self.window = window
        self.evaluation = Evaluation(window)
