#! /usr/bin/env python3
#! -*- coding:utf-8 -*-

class SysInfo():

    def __init__(self, conn):
        self.conn = conn

        self._info_cmd = {
            'net': ["ip addr | grep -E ' en| eth' "],
            'factory': ["dmidecode -t system | grep -E 'Manufacturer|Product Name|Serial Number'"],
            'cpu': ['dmidecode -t processor | grep -E "Socket Designation:|Version:|Core Count:|Thread Count:"'],
            'mem': ['free -b', 'dmidecode | grep "Maximum Capacity"'],
            'disk': ['parted -l | grep "Disk /"'],
        }

        self._info_tools= {
                'dmidecode': 'sudo apt install -y dmidecode',
                'parted': 'sudo apt install -y parted'
        }

    def _check_info_tools(self):
        print('[+] Checking dependency tools ... ', end = '')
        install_error = False
        for tool in self._info_tools.keys():
            i, o, e = self.conn.exec_command(f'command -v {tool} || {self._info_tools[tool]}')
            if o.channel.recv_exit_status() != 0:
                install_error = True
                print('[✗]')
                print(f'[x] Cannot install {tool} using "{self._info_tools[tool]}"!')
        if not install_error: print('[✓]')

    def get(self, infokinds):

        if len(infokinds) == 0:
            infokinds = self._info_cmd.keys()

        self._check_info_tools()

        info = {}
        for kind in infokinds:
            cmds = self._info_cmd[kind]
            cmds_output = []
            for cmd in cmds:
                i, o, e = self.conn.exec_command(cmd)
                cmds_output += o.readlines()
                if o.channel.recv_exit_status() != 0:
                    error = ''.join(e.readlines())
                    print(f'[x] CommandError => {cmd}\n\t{error}', end = '')
            info[kind] = cmds_output
        return info

    def purify(self, kind, verbose):
        purify_info = {}

        if kind == 'net':
            # TODO(bugnofree 2019-07-24) Purify net information
            pass

        purify_info['verbose'] = verbose

        if kind == 'factory':
            for line in verbose:
                key, value = line.split(':')
                key, value = key.strip(), value.strip()
                purify_info[key] = value

        if kind == 'cpu':
            cpu_logic_core_count = 0
            for line in verbose:
                key, value = line.split(':')
                if key.strip() == 'Thread Count':
                    cpu_logic_core_count += int(value.strip())
            purify_info['logic_core_count'] = cpu_logic_core_count

        if kind == 'mem':
            for line in verbose:
                if line.strip().startswith('Mem:'):
                    mem = line.strip().split()[1]
                    purify_info['total'] = int(mem)
                    break

        if kind == 'disk':
            total_size = 0
            for line in verbose:
                cap = line.strip().split(':')[1].strip()
                if cap.endswith('GB'):
                    total_size += int(float(cap[:-2]) * 1024 * 1024 * 1024)
            purify_info['size'] = total_size

        return purify_info
