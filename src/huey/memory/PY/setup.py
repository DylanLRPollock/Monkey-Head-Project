# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Setup module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
import os

from setuptools import find_packages, setup  # type: ignore

here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Long description could not be read from README.md"

setup(
    name="monkey-head-project",
    version="1.0.1",
    description="A project integrating diverse functionalities including ML, web frameworks, and more.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Dylan L.R. Pollock",
    author_email="admin@dlrp.ca",
    url="https://github.com/DylanLRPollock/Monkey-Head-Project",
    packages=find_packages(where="hueyos"),
    package_dir={"": "hueyos"},
    install_requires=[
        "requests==2.33.0",
        "httpx==0.28.1",
        "aiohttp==3.14.1",
        "websockets==15.0.1",
        "numpy==2.3.0",
        "scipy==1.15.3",
        "scikit-learn==1.7.0",
        "torch==2.12.0",
        "tensorflow==2.19.0",
        "transformers==5.0.0rc3",
        "pandas==2.3.0",
        "matplotlib==3.10.3",
        "seaborn==0.13.2",
        "plotly==6.1.2",
        "openpyxl==3.1.5",
        "sqlalchemy==2.0.41",
        "pymongo==4.13.1",
        "redis==6.2.0",
        "cryptography==49.0.0",
        "pyjwt==2.13.0",
        "bcrypt==4.3.0",
        "paramiko==5.0.0",
        "docker==7.1.0",
        "kubernetes==33.1.0",
        "fastapi==0.115.12",
        "uvicorn==0.34.3",
        "starlette==1.3.1",
        "flask==3.1.3",
        "python-vlc==3.0.21203",
        "psutil==7.0.0",
        "platformdirs==4.3.8",
        "py-cpuinfo==9.0.0",
        "pyttsx3==2.98",
        "deepspeech==0.9.3",
        "PyQt6==6.9.1",  # Choose one: PyQt6 or PySide6
        "PySimpleGUI==5.0.8.3",
        "boto3==1.38.35",
        "google-auth==2.40.3",
        "elasticsearch==9.0.2",
        "pyyaml==6.0.2",
        "pypdf>=5.1.0,<7.0.0",
        "pygpt-net>=2.7.12",
    ],
    extras_require={
        "dev": ["black==26.3.1", "flake8==6.0.0", "mypy==1.5.1", "pytest==9.0.3"]
    },
    python_requires=">=3.12",
    classifiers=[
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={"console_scripts": ["monkey-head=huey.cli:run_cli"]},
)
