#!/usr/bin/env python
# encoding: utf-8

from distutils.core import setup
from os import path

import isperdal
isperdal

setup(
    name='isperdal',
    version='0.1',
    description='a web framework.',
    author='quininer kel',
    author_email='quininer@live.com',
    url='https://github.com/quininer/isperdal',
    license='MIT',
    long_description=open(path.join(
        path.split(path.abspath(__file__))[0],
        'README.md'
    )).read(),
    packages=['isperdal', 'isperdal/middleware'],
    requires=['aiohttp']
)
