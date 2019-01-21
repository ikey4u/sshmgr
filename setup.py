#! /usr/bin/env python3
#! -*- coding:utf-8 -*-

from setuptools import setup, find_packages

setup (
    name = 'sshmgr',
    version = '1.0',
    author = 'bugnofree',
    author_email = 'pwnkeeper@gmail.com',
    url = 'https://github.com/ikey4u/sshmgr',
    description = 'A powerful ssh manager',
    long_description = open('README.md').read(),
    packages = ['sshmgr'],
    package_dir = {'sshmgr': 'sshmgr'},
    entry_points = {
        'console_scripts' : [
            'sshmgr = sshmgr:main'
            ]
    }
)
