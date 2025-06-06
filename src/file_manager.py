# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import shutil

from .error_handler import ErrorHandler


class FileManager:
    def move_file(self, src, dst):
        try:
            shutil.move(src, dst)
        except Exception as e:
            ErrorHandler().handle_exception(e)

    def read_file(self, file_path):
        try:
            with open(file_path, "r") as file:
                return file.read()
        except Exception as e:
            ErrorHandler().handle_exception(e)
            return None

    def write_file(self, file_path, content):
        try:
            with open(file_path, "w") as file:
                file.write(content)
        except Exception as e:
            ErrorHandler().handle_exception(e)
