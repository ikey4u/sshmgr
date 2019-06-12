#! /usr/bin/env python3
#! -*- coding:utf-8 -*-

from setuptools import setup, find_packages

with open('src/__VERSION__', 'r') as _:
    VERSION = _.readline().strip()

setup (
    name = 'sshmgr',
    version = VERSION,
    author = 'bugnofree',
    author_email = 'pwnkeeper@gmail.com',
    url = 'https://github.com/ikey4u/sshmgr',
    description = 'A powerful ssh manager',
    long_description_content_type='text/markdown',
    long_description = open('README.md').read(),

    python_requires = '>=3.6.0',
    install_requires = ['paramiko'],

    package_dir = {'sshmgr': 'src'},
    packages = ['sshmgr'],
    include_package_data=True,

    zip_safe = False,

    entry_points = {
        'console_scripts' : [
            'sshmgr = sshmgr.__main__:main'
            ]
    },
)
