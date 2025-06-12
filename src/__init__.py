import importlib
import sys

_pkg = importlib.import_module("monkey_head")
__path__ = _pkg.__path__
sys.modules[__name__] = _pkg
