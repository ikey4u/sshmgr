#! /usr/bin/env python3
#! -*- coding:utf-8 -*-

import argparse
import os
import sys

from .ssh import SSH
from . import util

def parse_docker_cmd(args):

    if not args.hosts:
        print('Require hosts parameters!')
        return

    hosts = list()

    flag_file = '@'
    flag_list = '/'
    if args.hosts.startswith(flag_file):
        hostpath = os.path.expanduser(args.hosts[len(flag_file):])
        if os.path.exists(hostpath):
            with open(hostpath, 'r') as _:
                lines = _.readlines()
                hosts += [l.strip('\n') for l in lines]
        else:
            print(f'[✗] Cannot open file => {hostpath}!')
    elif args.hosts.startswith(flag_list):
        hosts.extend([h.strip() for h in args.hosts[len(flag_list):].split(',') if h.strip()])
    else:
        hosts.append(args.hosts)

    for curhost in hosts:
        haserr = False
        ssh = None
        print(f'[+] Connect to {curhost} ... ', end = '')
        try:
            if args.enable_nvidia:
                ssh = SSH(curhost, dockerprog = 'nvidia-docker')
            else:
                ssh = SSH(curhost, dockerprog = 'docker')
        except Exception as e:
            print('✗')
            print(f"[✗] Cannot connect to {curhost}, errors:")
            print(str(e))
            haserr = True

        if haserr:
            continue
        else:
            print('✓')

        if args.new:
            print(f'[+] Add docker for user {args.new} on {curhost} ...')
            dckrinfo, ok = ssh.newdckr(args.new, apt = args.apt,
                    dockerfile = args.fdocker,
                    himsg = args.himsg,
                    portnum = args.portnum,
                    specport = args.require_ports)
            if ok:
                if not dckrinfo:
                    print('[✗] Cannot get the user inforamtion !')
                else:
                    infomsg = "Now you can use 'ssh {user:s}@{ip:s} -p {sshport:d}' and password '{psd:s}' to login.".format(
                        user = dckrinfo['user'],
                        ip = dckrinfo['ip'],
                        sshport = dckrinfo['sshport'],
                        psd = dckrinfo['psd']
                        )
                    print(infomsg)
                    if len(dckrinfo['xport']) > 0:
                        portstr = ','.join([str(i) for i in dckrinfo['xport']])
                        print("Your extra available ports are: {xport:s}".format(xport = portstr))
            else:
                ssh.deldckr(args.new)
                print(f'Cannot make docker for {args.new}!')
        elif args.delete:
            print (f'[+] Removing docker of {args.delete} from {curhost} ... ', end = '')
            try:
                if ssh.deldckr(args.delete):
                    print('[✓]')
                else:
                    print('[✗]')
            except Exception as e:
                print(f'[ERROR]: {str(e)}')
        elif args.query:
            print(f'[+] Query {args.query} on host {curhost} ... ')
            userinfo = ssh.get_userinfo(args.query)
            if userinfo is not None:
                print(f"  User             name: {userinfo['user']}")
                print(f"  User           xports: {userinfo['xport']}")
                print(f"  User         SSH port: {userinfo['sshport']}")
                print(f"  User default password: {userinfo['psd']}")
            else:
                print(f"[!] The user {args.query} does not exist on {curhost}!")
        elif args.list:
            users = ssh.get_userinfo()
            print(f'[+] User list for {curhost}:')
            if users is not None:
                for user in users.keys():
                    print(users[user])
            else:
                print('[!] No user found!')

def main():

    parser = argparse.ArgumentParser(prog = 'sshmgr', description = "A powerful linux server manager")
    parser.add_argument('-v', '--version', action = 'version', version = util.get_version(),
            help = 'Show the version of sshmgr')
    parser.add_argument('--hosts', nargs = '?', metavar = 'hosts', type = str,
            help = 'The host(s) to be operated on')
    parser.add_argument('--sshkey',  type = str, metavar = 'path_of_the_new_ssh_key',
            help = 'Update ssh key for administrator')

    subparsers = parser.add_subparsers(dest = 'has_docker_cmd')

    docker_cmd_parser = subparsers.add_parser('docker')
    docker_args_group = docker_cmd_parser.add_mutually_exclusive_group(required = True)
    docker_args_group.add_argument('--new', type = str,
            metavar = 'username',
            action = 'store',
            help = 'The user to add')
    docker_args_group.add_argument('--delete', type = str,
            metavar = 'username',
            action = 'store',
            help = 'The user to delete')
    docker_args_group.add_argument('--query', type = str,
            metavar = 'username',
            action = 'store',
            help = 'Query the information of username')
    docker_args_group.add_argument('--list', action = 'store_true',
            help = 'List all users in the host.')
    docker_cmd_parser.add_argument('--fdocker', metavar = 'dockerfile',
            type = str,
            action = 'store',
            default = '',
            help = 'The file path to dockerfile, the first line of the file must be `FROM ubuntu:16.04`')
    docker_cmd_parser.add_argument('--nvidia',
            action = 'store_true',
            dest = 'enable_nvidia',
            help = 'Enable gpu based nvidia docker')
    docker_cmd_parser.add_argument('--require-ports',
            metavar = 'the_required_ports',
            nargs = '+',
            type = int, # make each port int type
            default = [],
            help = 'The required ports exposed on host for your user.')
    docker_cmd_parser.add_argument('--portnum',
            metavar = 'the_number_of_port',
            type = int,
            default = 3,
            help = 'The required ports exposed on host for your user.')
    docker_cmd_parser.add_argument('--apt',
            choices = ['ubuntu.16.04.offical', 'ubuntu.16.04.tsinghua'],
            default = 'ubuntu.16.04.offical',
            help = 'Select apt source.list, the default is ubuntu.16.04.offical')
    docker_cmd_parser.add_argument('--himsg', metavar = 'hello_message',
            default = 'Your identifier is:',
            type = str,
            help = 'Messages showed after your guest logined into the server')

    args = parser.parse_args()

    if args.has_docker_cmd:
        parse_docker_cmd(args)
    elif args.sshkey:
            ok = ssh.change_sshkey(args.sshkey)
            if ok:
                print(f"[✓] Change ssh key for {curhost} successfully!")
            else:
                print(f"[✗] Some error happend when changed ssh key for {curhost}!")
    else:
        parser.print_usage()

if __name__ == "__main__":
    main()
