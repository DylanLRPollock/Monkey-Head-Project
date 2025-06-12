#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2025.02.25 00:00:00                  #
# ================================================== #

import os
import pyttsx3

from .base import BaseProvider


class OfflineTextToSpeech(BaseProvider):
    def __init__(self, *args, **kwargs):
        """Offline Text to Speech provider"""
        super(OfflineTextToSpeech, self).__init__(*args, **kwargs)
        self.plugin = kwargs.get("plugin")
        self.id = "offline_tts"
        self.name = "Offline TTS"

    def init_options(self):
        """Initialize options (none required)"""
        pass

    def speech(self, text: str) -> str:
        """Speech text to audio using pyttsx3"""
        output_file = self.plugin.output_file
        path = os.path.join(
            self.plugin.window.core.config.path,
            output_file,
        )
        engine = pyttsx3.init()
        engine.save_to_file(text, path)
        engine.runAndWait()
        return path

    def is_configured(self) -> bool:
        """Check if provider is configured"""
        try:
            import pyttsx3  # noqa: F401
            return True
        except ImportError:
            return False

    def get_config_message(self) -> str:
        """Return message to display when provider is not configured"""
        return "pyttsx3 is required for Offline TTS. Please install it."
