#! /usr/bin/env python3
#! -*- coding:utf-8 -*-

import time
import os

import paramiko

from . import util

dckrtpl = """\
FROM ubuntu:16.04
COPY {sourcelist:s} {init:s} {motd:s} {sprvsr:s} /tmp/
RUN bash /tmp/{init} {user:s} /tmp/{sourcelist} /tmp/{motd} /tmp/{sprvsr} {psdlen:d}
{content:s}
SHELL ["/bin/bash", "-c"]
ENTRYPOINT "/usr/bin/supervisord"
"""

init = """\
#! /bin/bash
user=$1
sourcelist=$2
motd=$3
sprvsr=$4
psdlen=$5

apt update && apt install -y wget ca-certificates apt-transport-https
cat $sourcelist > /etc/apt/sources.list && apt update
mkdir -p /$user/.ssh/ && mkdir -p /var/run/sshd && mkdir -p /var/log/supervisor
apt install -y openssh-server vim supervisor sudo locales pwgen

useradd -d /home/$user -m -s /bin/bash $user
usermod -aG sudo $user

echo "LC_ALL=en_US.UTF-8" >> /etc/environment
echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
echo "LANG=en_US.UTF-8" > /etc/locale.conf
locale-gen en_US.UTF-8

rm -rf /etc/update-motd.d/*
cat $motd > /etc/update-motd.d/00-sshmgr-sayhello
chmod +x /etc/update-motd.d/00-sshmgr-sayhello

cat $sprvsr > /etc/supervisor/conf.d/supervisord.conf

psd=$(pwgen -N 1 $psdlen) && echo "$user:$psd" | chpasswd
echo $psd > /home/$user/.defpsd
"""

motdfmt = """\
#! /bin/bash
echo --------------------------------------------------------------------
echo
echo "         _                          ";
echo "        | |                         ";
echo " ___ ___| |__  _ __ ___   __ _ _ __ ";
echo "/ __/ __| '_ \| '_ \` _ \ / _\` | '__|";
echo "\__ \__ \ | | | | | | | | (_| | |   ";
echo "|___/___/_| |_|_| |_| |_|\__, |_|   ";
echo "                          __/ |     ";
echo "                         |___/      ";
echo
echo [Powered by sshmger, see https://github.com/ikey4u/sshmgr for more infomation]
echo
echo --------------------------------------------------------------------
echo {himsg}
echo ID: {hostid:s}:{user}
echo --------------------------------------------------------------------
"""

sprvsrfile = """\
[supervisord]
nodaemon=true
[program:sshd]
command=/usr/sbin/sshd -D
"""

def build(conn: paramiko.SSHClient, **extra) -> bool:
    '''Build a general docker

    :conn: An established paramiko connection.
    :extra: Extra information.
        {
            'dockerprog': The docker program.
            'user': The user name.
            'hostid': The host where the docker is built in.
            'content': The customized docker file content.
            'himsg': The hello message from the administrator.
            'apg': The apt souce type.
        }

    :return: if build successfully, return true, or else false.
    '''

    tm = str(time.time())
    sftp = conn.open_sftp()

    with sftp.file(f"/tmp/{tm}.sourcelist", "w") as srcfile:
        with open(os.path.join(util.get_data_root(), 'ubuntu', extra['apt']), 'r') as _:
            srcfile.write(_.read())
    with sftp.file(f"/tmp/{tm}.motd", "w") as _:
        _.write(motdfmt.format(himsg = extra['himsg'], user = extra['user'], hostid = extra['hostid']))
    with sftp.file(f"/tmp/{tm}.supervisord", "w") as _:
        _.write(sprvsrfile)
    with sftp.file(f"/tmp/{tm}.init", "w") as _:
        _.write(init)
    with sftp.file(f"/tmp/{tm}.dockerfile", "w") as _:
        dockerfile = dckrtpl.format(content = extra['content'],
                sourcelist = f"{tm}.sourcelist",
                init = f"{tm}.init",
                motd = f"{tm}.motd",
                sprvsr = f"{tm}.supervisord",
                user = f"{extra['user']}",
                psdlen = 15)
        _.write(dockerfile)
    sftp.close()

    docker_build_cmd = (f'{extra["dockerprog"]} build'
        f' --tag {extra["hostid"]}:{extra["user"]}'
        f' --file /tmp/{tm}.dockerfile /tmp')
    print(f"[+] {docker_build_cmd}")
    stdin, stdout, stderr = conn.exec_command(docker_build_cmd)
    err = stdout.channel.recv_exit_status()
    # Remove unused files
    conn.exec_command(f'rm -rf /tmp/{tm}.*')
    if err:
        print("[x] Cannot run docker build!")
        for line in stderr.readlines():
            print(line.strip('\n'))
        conn.close()
        return False
    else:
        return True
