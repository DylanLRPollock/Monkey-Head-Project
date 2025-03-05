import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Long description could not be read from README.md"

setup(
    name='MonkeyHeadProject',
    version='1.0.0',
    description='A project integrating diverse functionalities including ML, web frameworks, and more.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Dylan L.R. Pollock',
    author_email='admin@dlrp.ca',
    url='https://github.com/DylanLRPollokc/Monkey-Head-Project',
    packages=find_packages(),
    install_requires=[
        'requests==2.32.3',
        'httpx==0.27.2',
        'aiohttp==3.11.11',
        'websockets==11.0.3',
        'numpy==1.26.4',
        'scipy==1.10.1',
        'scikit-learn==1.3.0',
        'torch==2.0.1',
        'tensorflow==2.13.0',
        'transformers==4.29.0',
        'pandas==2.2.3',
        'matplotlib==3.7.1',
        'seaborn==0.12.2',
        'plotly==5.14.1',
        'openpyxl==3.1.2',
        'sqlalchemy==2.0.37',
        'pymongo==4.3.3',
        'redis==5.2.1',
        'cryptography==44.0.0',
        'pyjwt==2.7.0',
        'bcrypt==4.0.1',
        'paramiko==3.1.0',
        'docker==7.1.0',
        'kubernetes==31.0.0',
        'fastapi==0.115.6',
        'uvicorn==0.23.2',
        'starlette==0.41.3',
        'psutil==5.9.5',
        'platformdirs==3.5.1',
        'py-cpuinfo==9.0.0',
        'PyQt6==6.5.1',  # Choose one: PyQt6 or PySide6
        'PySimpleGUI==4.60.4',
        'boto3==1.36.0',
        'google-auth==2.37.0',
        'elasticsearch==8.17.0',
        'pygpt-net>=0.1.0'
    ],
    extras_require={
        'dev': [
            'black==23.7.0',
            'flake8==6.0.0',
            'mypy==1.5.1',
            'pytest==7.4.0'
        ]
    },
    python_requires='>=3.11',
    classifiers=[
        'Programming Language :: Python :: 3.11',
        'Operating System :: Microsoft :: Windows',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'console_scripts': [
            'monkeyhead=monkeyhead.cli:main'
        ]
    },
)
