#! /usr/bin/env python3
#! -*- coding:utf-8 -*-

import os
from inspect import getframeinfo,stack

def get_data_root():
    dataroot = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(dataroot, 'data')

def get_proj_root():
    rootpath = os.path.abspath(os.path.dirname(__file__))
    return rootpath

def get_version():
    with open(os.path.join(get_proj_root(), '__VERSION__'), 'r') as _:
        return _.readline().strip()

def dbgprint(msg):
    caller = getframeinfo(stack()[1][0])
    print("[DBGINFO] ==> [%s -> %s -> %d]\n\t%s" %
         (caller.filename, caller.function, caller.lineno, msg))

