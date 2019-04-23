---
Title: sshmgr
Date: 2019-04-23
Author: bugnofree
---

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
    - The client should install `paramiko` package installed

# Installation

Download the source, uncompress it and enter the source directory. Run the following command to install

    python3 setup.py install

# Quick start

    ➜  sshmgr (master) ✔ sshmgr -h
    usage: sshmgr [-h] [-H HOSTID [HOSTID ...]] [--fdocker FDOCKER]
                  [--docker DOCKER] [-v] [-u USER] [-l] [-k KEY]
                  [-x {newdckr,deldckr,getinfo}]

    A powerful linux server manager

    optional arguments:
      -h, --help            show this help message and exit
      -H HOSTID [HOSTID ...], --hostid HOSTID [HOSTID ...]
                            The ssh host ID
      --fdocker FDOCKER     The file path to dockerfile, the firstline of the file
                            must be `FROM ubuntu:16.04`
      --docker DOCKER       The main docker command such as `docker` or `nvidia-
                            docker` to start docker, the default is `docker`
      -v, --version         Show the version of sshmgr
      -u USER, --user USER  The user name
      -l, --list            List all users on the server
      -k KEY, --key KEY     The new key for the master
      -x {newdckr,deldckr,getinfo}
                            The action to execute for the user

You could add multiple host IDs with space separated. You can give two special ID to easy
your task:

- `003..005` In this case, sshmgr will iterate 003, 004 and 005.
- `@/path/to/ids` In this case, sshmgr will open `/path/to/ids` (where one id holds in one line),
    and iterates the ids.
