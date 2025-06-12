#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2024.08.25 06:00:00                  #
# ================================================== #

from unittest.mock import MagicMock

from tests.mocks import mock_window
from pygpt_net.controller.idx.common import Common


def test_setup(mock_window):
    """Test setup"""
    checkbox = MagicMock()
    mock_window.ui.config = {'global': {'llama.idx.raw': checkbox}}
    mock_window.core.config.get = MagicMock(return_value=True)
    common = Common(mock_window)
    common.setup()
    checkbox.setChecked.assert_called_once_with(True)


def test_toggle_raw(mock_window):
    """Test toggle_raw"""
    mock_window.core.config.set = MagicMock()
    mock_window.core.config.save = MagicMock()
    common = Common(mock_window)
    common.toggle_raw(True)
    mock_window.core.config.set.assert_called_once_with('llama.idx.raw', True)
    mock_window.core.config.save.assert_called_once()
