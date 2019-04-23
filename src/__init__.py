#! /usr/bin/env python3
#! -*- coding:utf-8 -*-

from .ssh import SSH

import argparse
import os
import sys

def main():
    ROOT = os.path.abspath(os.path.dirname(__file__))

    parser = argparse.ArgumentParser(description = "A powerful linux server manager")
    parser.add_argument("-H", "--hostid", nargs = "+", help = "The ssh host ID", type = str)
    parser.add_argument("--fdocker", default = '', type = str,
            help = "The file path to dockerfile, the firstline of the file must be `FROM ubuntu:16.04`")
    parser.add_argument("--docker", default = "docker", type = str,
            help = "The main docker command such as `docker` or `nvidia-docker` to start docker, the default is `docker`")
    parser.add_argument("-v", "--version", action="store_true", help = "Show the version of sshmgr")
    parser.add_argument("-u", "--user", help = "The user name", type = str)
    parser.add_argument("-l", "--list", help = "List all users on the server", action='store_true')
    parser.add_argument("-k", "--key", help = "The new key for the master", type = str)
    parser.add_argument("-x", choices = ["newdckr", "deldckr", "getinfo"],
            help = "The action to execute for the user", type = str)
    args = parser.parse_args()

    if args.version:
        with open(os.path.join(ROOT, '__VERSION__'), 'r') as _:
            print(_.readline().strip())
        return

    if not args.hostid:
        parser.print_help()
        return

    host = list()
    for h in args.hostid:
        if h.startswith('@'):
            h = os.path.expanduser(h[1:])
            if os.path.exists(h):
                with open(h, 'r') as _:
                    lines = _.readlines()
                    host += [l.strip('\n') for l in lines]
        elif len(h.split('..')) == 2:
            beg, end = h.split('..')[0], h.split('..')[1]
            for i in range(int(beg), int(end) + 1, 1):
                host.append(f'{str(i):>0{len(beg)}}')
        else:
            host.append(h)

    for curhost in host:
        haserr = False
        ssh = None
        try:
            ssh = SSH(curhost, docker = args.docker)
        except Exception as e:
            print(str(e))
            print(f"{curhost} Connection Error! Skipped!")
            haserr = True
        if haserr: continue

        if args.user:
            if args.x == "newdckr":
                dckrinfo, ok = ssh.newdckr(args.user, portnum = 3, dockerfile = args.fdocker)
                if ok:
                    if dckrinfo is None:
                        print('[*] Cannot get the user inforamtion !')
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
                    ssh.deldckr(args.user)
                    print("Cannot make docker for the user!")
            elif args.x == "deldckr":
                print (f'[+] Removing docker of {args.user} ... ', end = '')
                try:
                    if ssh.deldckr(args.user):
                        print('[OK]')
                    else:
                        print('[X]')
                except Exception as e:
                    print('[x]')
                    print(f'ERROR: {str(e)}')
            elif args.x == "getinfo":
                userinfo = ssh.get_userinfo(args.user)
                if userinfo is not None:
                    print(f"User             name: {userinfo['user']}")
                    print(f"User           xports: {userinfo['xport']}")
                    print(f"User         SSH port: {userinfo['sshport']}")
                    print(f"User default password: {userinfo['psd']}")
                else:
                    print("User does not exist!")
            else:
                print("[x] Unknown action!")
                parser.print_usage()
        elif args.list:
            users = ssh.get_userinfo()
            if users is not None:
                for user in users.keys():
                    print(users[user])
            else:
                print('[!] No user found!')
        elif args.key:
            ok = ssh.change_sshkey(args.key)
            if ok:
                print(f"[OK] Change ssh key for {curhost} successfully!")
            else:
                print(f"[x] Some error happend when changed ssh key for {curhost}!")
        else:
            parser.print_usage()

if __name__ == "__main__":
    main()
