# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: File Manager module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
import shutil

from .error_handler import ErrorHandler


class FileManager:
    """Helper for basic file operations with unified error handling."""

    def move_file(self, src: str, dst: str) -> None:
        """Move a file from ``src`` to ``dst``."""

        try:
            shutil.move(src, dst)
        except Exception as e:  # pragma: no cover - simple wrapper
            ErrorHandler().handle_exception(e)

    def read_file(self, file_path: str, encoding: str = "utf-8") -> str | None:
        """Return the contents of ``file_path`` or ``None`` on error."""

        try:
            with open(file_path, "r", encoding=encoding) as file:
                return file.read()
        except Exception as e:  # pragma: no cover - simple wrapper
            ErrorHandler().handle_exception(e)
            return None

    def write_file(self, file_path: str, content: str, encoding: str = "utf-8") -> None:
        """Write ``content`` to ``file_path``."""

        try:
            with open(file_path, "w", encoding=encoding) as file:
                file.write(content)
        except Exception as e:  # pragma: no cover - simple wrapper
            ErrorHandler().handle_exception(e)
