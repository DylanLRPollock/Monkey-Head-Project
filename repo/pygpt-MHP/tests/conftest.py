import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Skip entire test suite if PySide6 is not available. These tests rely heavily
# on Qt widgets and will fail to import without the dependency installed.
try:  # pragma: no cover - only used for test environment configuration
    import PySide6  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - only used for test environment configuration
    pytest.skip("PySide6 is required for pygpt-MHP tests", allow_module_level=True)


@pytest.fixture(scope='session', autouse=True)
def set_env_vars():
    os.environ['ENV_TEST'] = '1'  # set env = test
    os.environ['TEST_LANGUAGE'] = 'en'  # force EN locale for tests
    yield
