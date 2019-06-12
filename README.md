             _
            | |
     ___ ___| |__  _ __ ___   __ _ _ __
    / __/ __| '_ \| '_ ` _ \ / _` | '__|
    \__ \__ \ | | | | | | | | (_| | |
    |___/___/_| |_|_| |_| |_|\__, |_|
                              __/ |
                             |___/

    [Powered by sshmger, see https://github.com/ikey4u/sshmgr for more infomation]

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

    python3 setup.py install

# Quick start

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
    ➜  sshmgr (master) ✗ sshmgr docker -h
    usage: sshmgr docker [-h]
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

More about `--hosts`.  You can process multiple hosts in one command, if the
host name

- case that beginning with `@`

    It indicates a file that contains multiple host ID, one ID holds one line.
    For example, `@$HOME/Downloads/hostids`.

- case that beginning with `/`

    The hosts are seperated by comma, for example `/tom, nancy, louis`.

- case that normal

    A single host name you want to connect to.

sshmgr will connect to your specified host and create a docker container for
your guest, create a `$HOME/share` folder shared between the user on host and the
user on the container.

# Development

Open a terminal at the project root, debug with `python3 -m src <options>`.
