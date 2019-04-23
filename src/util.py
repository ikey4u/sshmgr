#! /usr/bin/env python3
#! -*- coding:utf-8 -*-

from inspect import getframeinfo,stack

class Util(object):
    """Util class for debug"""

    # User may set ENABLE_DBG to False to disable debug information
    ENABLE_DBG = True

    @staticmethod
    def print(msg):
        """Function for printing debug information"""

        if(not Util.ENABLE_DBG):return
        caller = getframeinfo(stack()[1][0])
        print("[DBGINFO] ==> [%s -> %s -> %d]\n\t%s" %
             (caller.filename, caller.function, caller.lineno, msg))
