# sshmgr - A powerful Linux server manager

It leverages docker to automatically do

- create a new ubuntu container for user, the current supported ubuntu base images are
    - ubuntu 16.04
- setup a default password located in user's `$HOME/.defpsd`
- setup a ssh login welcome message

It supports `docker` for normal docker creation and `nvidia-docker` for gpu docker creation.
The dockerfile for nvidia based gpu could be found here
@[https://gitlab.com/nvidia/cuda].

You can specify a customized `dockerfile` with first line beginning with `FROM ubuntu:<supported ubuntu version>`.

# Dependencies

- Server Side
    - The Linux server should have docker installed
- Client Side
    - The client should have `~/.ssh/config` configured
    - The client should have `paramiko` package installed

# Installation

Download the source, uncompress it and enter the source directory. Run the following command to install

    pip3 install sshmgr

# Quick start

## Main interface

    ➜  sshmgr (master) ✗ sshmgr -h
    usage: sshmgr [-h] [-v] [--hosts [hosts]] [--sshkey path_of_the_new_ssh_key]
                  {docker} ...

    A powerful linux server manager

    positional arguments:
      {docker}

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         Show the version of sshmgr
      --hosts [hosts]       The host(s) to be operated on
      --sshkey path_of_the_new_ssh_key
                            Update ssh key for administrator

More about `--hosts`.  You can process multiple hosts in one command, if the
host name

- case that beginning with `@`

    It indicates a file that contains multiple host ID, one ID holds one line.
    For example, `@$HOME/Downloads/hostids`.

    Empty lines will be ignored and lines begin with `#` will be regarded as
    comments.

- case that beginning with `/`

    The hosts are seperated by comma, for example `/tom, nancy, louis`.

- case that a normal host

    A single host name you want to connect to.

## The docker interface

    sshmgr --hosts <hosts> docker [-h]
                         (--new username | --delete username | --query username | --list)
                         [--fdocker dockerfile] [--nvidia]
                         [--apt {ubuntu.16.04.offical,ubuntu.16.04.tsinghua}]
                         [--himsg hello_message]

    optional arguments:
      -h, --help            show this help message and exit
      --new username        The user to add
      --delete username     The user to delete
      --query username      Query the information of username
      --list                List all users in the host.
      --fdocker dockerfile  The file path to dockerfile, the first line of the
                            file must be `FROM ubuntu:16.04`
      --nvidia              Enable gpu based nvidia docker
      --apt {ubuntu.16.04.offical,ubuntu.16.04.tsinghua}
                            Select apt source.list, the default is
                            ubuntu.16.04.offical
      --himsg hello_message
                            Messages showed after your guest logined into the
                            server

sshmgr will connect to your specified host and create a docker container for
your guest, create a `$HOME/share` folder shared between the user on host and the
user on the container.

## The info interface

Retrieve server information:

    sshmger --hosts <hosts> info [-h]
        [--net Network]
        [--factory Manufacturer]
        [--cpu CPU]
        [--mem Memory]
        [--disk Disk]

An example is showed as below:

    "102": {
        "info": {
            "net": {
                "verbose": [
                    "2: enp2s0f0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000\n",
                    "    inet 192.168.100.102/24 brd 192.168.100.255 scope global enp2s0f0\n"
                ]
            },
            "factory": {
                "verbose": [
                    "\tManufacturer: xxx\n",
                    "\tProduct Name: xxx V3\n",
                    "\tSerial Number: xxx\n"
                ],
                "Manufacturer": "xxx",
                "Product Name": "xxx V3",
                "Serial Number": "xxx"
            },
            "cpu": {
                "verbose": [
                    "\tSocket Designation: CPU01\n",
                    "\tVersion: Intel(R) Xeon(R) CPU E5-2630 v3 @ 2.40GHz\n",
                    "\tCore Count: 8\n",
                    "\tThread Count: 16\n",
                    "\tSocket Designation: CPU02\n",
                    "\tVersion: Intel(R) Xeon(R) CPU E5-2630 v3 @ 2.40GHz\n",
                    "\tCore Count: 8\n",
                    "\tThread Count: 16\n"
                ],
                "logic_core_count": 32
            },
            "mem": {
                "verbose": [
                    "              total        used        free      shared  buff/cache   available\n",
                    "Mem:      131626576      577188   130605988        9304      443400   130449412\n",
                    "Swap:     133803004           0   133803004\n",
                    "\tMaximum Capacity: 2 TB\n"
                ],
                "total": 131626576
            },
            "disk": {
                "verbose": [
                    "Disk /dev/sda: 1198GB\n"
                ],
                "size": 1286342705152
            }
        },
        "errmsg": null,
        "status": false
    }

Both memory and disk size are in bytes.

If you want to process further, for example, you want to have an overview of the
servers in `cpu`, `memory`, `disk`, you can use the following code snippets:

    #! /usr/bin/env python3
    #! -*- coding:utf-8 -*-

    import json

    with open('sysinfo.json', 'r') as _:
        sysinfo = json.load(_)

    cpucnt, memsz, disksz = 0, 0, 0
    for host in sysinfo.keys():
        if not sysinfo[host]['islive']: continue
        cpucnt += sysinfo[host]['info']['cpu']['logic_core_count']
        memsz += sysinfo[host]['info']['mem']['total']
        disksz += sysinfo[host]['info']['disk']['size']

    print(f'[+] CPU Count: {cpucnt} Memory Size: {memsz/(1024 ** 3)} GB Disk Size: {disksz/(1024 ** 4)} TB')

# Development

Open a terminal at the project root, debug with `python3 -m src <options>`.
