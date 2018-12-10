# sshmgr - A powerful linux server manager

    ➜  sshmgr (master) ✔ python3 sshmgr.py -h
    usage: sshmgr.py [-h] [-u USER] [-x {newdckr,deldckr,getinfo}] hostid

    A powerful linux server manager

    positional arguments:
      hostid                The ssh host ID

    optional arguments:
      -h, --help            show this help message and exit
      -u USER, --user USER  The user name
      -x {newdckr,deldckr,getinfo}
                            The action to execture

# Installation

Download the source, uncompress it and enter the source directory. Run `make` and you are done.

# Quick start

    ➜  sshmgr (master) ✗ sshmgr -h
    usage: sshmgr [-h] [-u USER] [-k KEY] [-x {newdckr,deldckr,getinfo,list}]
                  hostid [hostid ...]

    A powerful linux server manager

    positional arguments:
      hostid                The ssh host ID

    optional arguments:
      -h, --help            show this help message and exit
      -u USER, --user USER  The user name
      -k KEY, --key KEY     The new key for the master
      -x {newdckr,deldckr,getinfo,list}
                            The action to execute for the user

You could add multiple host IDs with space separated. You can give two special ID to easy
your task:

- `003..005` In this case, sshmgr will iterate 003, 004 and 005.
- `@/path/to/ids` In this case, sshmgr will open `/path/to/ids` (where one id holds in one line),
    and iterates the ids.
