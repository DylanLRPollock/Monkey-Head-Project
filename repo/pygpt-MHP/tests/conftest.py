import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Skip entire test suite if required optional dependencies are missing.
# The project's tests rely on a number of heavy libraries.  When running in
# minimal environments (such as this repository), these libraries may not be
# installed which would cause ImportError exceptions during collection.  To
# avoid noisy failures we check for their presence up front and skip the suite
# entirely if any are unavailable.
required_modules = [
    "PySide6",
    "overrides",
    "SpeechRecognition",
    "sqlalchemy",
    "tiktoken",
    "pyaudio",
    "docker",
    "bs4",
    "httpx_socks",
    "llama_index",
    "langchain_openai",
    "langchain_community",
]

missing = []
for module in required_modules:
    try:  # pragma: no cover - only used for test environment configuration
        __import__(module)
    except ModuleNotFoundError:  # pragma: no cover - only used for test env configuration
        missing.append(module)

if missing:  # pragma: no cover - only used for test environment configuration
    pytest.skip(
        "Required test dependencies missing: " + ", ".join(sorted(missing)),
        allow_module_level=True,
    )


@pytest.fixture(scope='session', autouse=True)
def set_env_vars():
    os.environ['ENV_TEST'] = '1'  # set env = test
    os.environ['TEST_LANGUAGE'] = 'en'  # force EN locale for tests
    yield
