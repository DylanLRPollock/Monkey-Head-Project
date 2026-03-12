#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Base module (huey/pygpt_net/provider/agents)

# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2024.12.14 22:00:00                  #
# ================================================== #

from typing import Any, Dict


class BaseAgent:
    def __init__(
        self,
        *args,
        agent_id: str = "",
        mode: str = "step",
        **kwargs,
    ):
        self.id = agent_id
        self.mode = mode  # step|plan

    def get_mode(self) -> str:
        """
        Return Agent mode

        :return: Agent mode
        """
        return self.mode

    def get_agent(self, window, kwargs: Dict[str, Any]):
        """
        Return Agent provider instance

        :param window: window instance
        :param kwargs: keyword arguments
        :return: Agent provider instance
        """
        raise NotImplementedError(
            "BaseAgent.get_agent() must be implemented in subclasses"
        )
