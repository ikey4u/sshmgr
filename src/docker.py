#! /usr/bin/env python3
#! -*- coding:utf-8 -*-

import re

import docker_general

class Docker:

    def __init__(self):
        self._docker = {
                'general': {
                    'build': self._build_general_docker,
                    'description': docstr('''
                        > general docker
                            Features:
                                - A
                                - B
                                    - C
                    ''')
                    }
                }

        print(self._docker['general']['description'])

    def build(self, docker_type):
        if docker_type == 'general':
            self._build_general_docker()
        elif docker_type == 'nvidia':
            self._build_nvidia_docker()
        else:
            print('[x] Unkonwn docker type!')

    def show_docker_type(self):
        pass


    def _build_nvidia_docker(self):
        pass
