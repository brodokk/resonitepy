import os
from distutils.core import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='neos.py',
    version='0.1',
    description='NeosVR API module',
    author='Alexander Terry, brodokk',
    author_email='alexterry43@gmail.com, brodokk@brodokk.space',
    url='https://github.com/brodokk/neos.py',
    packages=['neos'],
    install_requires=required,
)
