#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Planner module (huey/pygpt_net/provider/agents)

# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2024.12.14 22:00:00                  #
# ================================================== #

from typing import Any, Dict

from llama_index.core.agent import (
    FunctionCallingAgentWorker,
    StructuredPlannerAgent,
)

from .base import BaseAgent


class PlannerAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super(PlannerAgent, self).__init__(
            *args, agent_id="planner", mode="plan", **kwargs
        )

    def get_agent(self, window, kwargs: Dict[str, Any]):
        """
        Return Agent provider instance

        :param window: window instance
        :param kwargs: keyword arguments
        :return: Agent provider instance
        """
        tools = kwargs.get("tools", [])
        verbose = kwargs.get("verbose", False)
        llm = kwargs.get("llm", None)
        chat_history = kwargs.get("chat_history", [])
        worker = FunctionCallingAgentWorker.from_tools(
            tools=tools,
            llm=llm,
            verbose=verbose,
        )
        return StructuredPlannerAgent(
            agent_worker=worker,
            llm=llm,
            chat_history=chat_history,
            tools=tools,
            verbose=verbose,
        )
