#! /usr/bin/env python3
#! -*- coding:utf-8 -*-

from setuptools import setup, find_packages

setup (
    name = 'sshmgr',
    version = '1.0',
    author = 'bugnofree',
    author_email = 'pwnkeeper@gmail.com',
    url = 'https://www.ahageek.com/sshmgr',
    description = 'A powerful ssh manager',
    long_description = open('README.md').read(),
    package_dir={'': '.'},
    packages=find_packages(),
    entry_points = {
        'console_scripts' : [
            'sshmgr = sshmgr:main'
            ]
    }
)
