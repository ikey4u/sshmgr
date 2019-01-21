#! /usr/bin/env python3
#! -*- coding:utf-8 -*-

import os
import sys
import random
import time
import json

import paramiko

dckrfmt = """\
FROM ubuntu:16.04
SHELL ["/bin/bash", "-c"]
COPY {sourcelist:s} {init:s} {motd:s} {sprvsr:s} /tmp/
RUN bash /tmp/{init} {user:s} /tmp/{sourcelist} /tmp/{motd} /tmp/{sprvsr} {psdlen:d}
ENTRYPOINT "/usr/bin/supervisord"
"""

sourcelist = """\
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial-backports main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial-security main restricted universe multiverse
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
echo ----------------------------------
echo Welcome {user:s} to HPDM Labs!
echo ID   : {hostid:s}:{user}
echo ----------------------------------
"""

sprvsrfile = """\
[supervisord]
nodaemon=true
[program:sshd]
command=/usr/sbin/sshd -D
"""

class SSH:
    """Manage the user with ssh key"""
    def __init__(self, hostid):
        self.hostid = hostid
        self.hostip = ""
        self.dockerdb = "/root/dockerdb/userdb.json"
        self.sshconf = os.path.expanduser('~/.ssh/config')

        if not os.path.exists(self.sshconf):
            print(f"[x] No config file found in {self.sshconf}!")
            sys.exit(1)

        # Check connection(only once for now)
        try:
            conn = self.__connect()
            conn.close()
        except Exception as e:
            raise Exception("Cannot connect to the server!")

    def __connect(self):
        config = paramiko.SSHConfig()
        with open(self.sshconf, 'r') as _: config.parse(_)
        hostopt = config.lookup(self.hostid)
        cfg = dict()
        cfg['hostname'] = hostopt['hostname']
        cfg['username'] = hostopt['user']
        cfg['port'] = hostopt['port']
        cfg['key_filename'] = hostopt['identityfile']
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(**cfg)
        self.hostip = hostopt['hostname']
        return ssh

    def getport(self):
        busy, free = set(), set(range(65536))
        conn = self.__connect()
        stdin, stdout, stderr = conn.exec_command('netstat -lnptu')
        # 'netstat -lnptu' returns what looks like below:
        #  Active Internet connections (only servers)
        #  Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
        #  tcp        0      0 127.0.0.1:27017         0.0.0.0:*               LISTEN      26111/mongod
        #  tcp        0      0 0.0.0.0:139             0.0.0.0:*               LISTEN      1924/smbd
        #  tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      19095/nginx -g daem
        #  tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      1629/sshd
        ipports = [l.split()[3] for l in stdout.readlines()[2:]]
        for ipport in ipports:
            busy.add(int(ipport.split(":")[-1]))
        free -= busy
        conn.close()
        return busy, free

    def rndport(self, num, specport = None, start = 1, end = 65536):
        """Random select port number

        :param num (int): The number of random ports.
        :param specport (list of ints): (optional) The must having ports in radmom generated ports.
        :return ports (list), status (bool):
        """

        # check specified port satisfaction
        if specport is None: specport = list()
        if len(specport) > num:
            print("[x] The specified ports number should less or equal to the total number of ports.")
            return None, False
        for p in specport:
            if p < start or p >= end:
                print("[x] The specified port is not in range!")
                return None, False
        busy, free = self.getport()
        takenports = busy & set(specport)
        if len(takenports) > 0:
            msg = ','.join([str(takenport) for takenport in takenports])
            print("[!] The following ports have been taken {:s}.".format(msg))
            return None, False

        satport = [i for i in free if i >= start and i < end]
        for p in specport:
            if p in satport:
                satport.remove(p)
        ports = list()
        for i in range(num - len(specport)):
            port = random.choice(satport)
            satport.remove(port)
            ports.append(port)
        ports.extend(specport)
        return ports, True

    def newuser(self, user, shell = '/bin/false'):
        flag = True
        conn = self.__connect()
        cmd = "useradd -d /home/{user:s} -m -s {shell:s} {user}".format(user = user,
                shell = shell)
        stdin, stdout, stderr = conn.exec_command(cmd)
        conn.close()
        return flag

    def is_user_exist(self, user):
        conn = self.__connect()
        cmd = "cat /etc/passwd | grep {user:s}: | wc -l".format(user = user.strip())
        stdin, stdout, stderr = conn.exec_command(cmd)
        lines = stdout.readlines()
        cnt = int(lines[0])
        conn.close()
        return False if cnt ==0 else True

    def hasimage(self, user):
        conn = self.__connect()
        cmd = f"docker image ls {self.hostid}:{user} | wc -l"
        # Return what looks like below:
        #  $ docker image ls | docker image ls vps:init
        #  REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
        #  vps                 init                1ab3352aab49        43 hours ago        345MB
        i, o, e = conn.exec_command(cmd)
        lines = o.readlines()
        cnt = int(lines[0])
        conn.close()
        return True if cnt >= 2 else False

    def get_dckrjar_list(self, user):
        conn = self.__connect()
        cmd = f"docker ps -a | grep {self.hostid}:{user}"
        i, o, e = conn.exec_command(cmd)
        lines = [l.strip('\n') for l in o.readlines()]
        jar = list()
        for line in lines:
            jar.append(line.split()[-1])
        conn.close()
        return jar

    def deldckr(self, user):
        conn = self.__connect()

        if self.is_user_exist(user) and self.hasimage(user):
            for jar in self.get_dckrjar_list(user):
                i, o, e = conn.exec_command(f"docker stop {jar} && docker rm {jar}")
                o.channel.recv_exit_status()
            i, o, e = conn.exec_command(f"docker rmi {self.hostid}:{user}")
            o.channel.recv_exit_status()

        if self.is_file_exist(self.dockerdb):
            sftp = conn.open_sftp()
            fuserdb = sftp.file(self.dockerdb, 'r')
            userdb = json.load(fuserdb)
            fuserdb.close()

            if user in userdb.keys(): del userdb[user]

            fuserdb = sftp.file(self.dockerdb, 'w')
            json.dump(userdb, fuserdb)
            fuserdb.close()
            sftp.close()

        i, o, e = conn.exec_command("yes | docker image prune")
        o.channel.recv_exit_status()

        i, o, e = conn.exec_command("yes | docker contanier prune")
        o.channel.recv_exit_status()

        conn.close()
        return True

    def newdckr(self, user, portnum = 0, specport = None):
        """Create a docker for user

        :param hostid (string): The identifier of the host.
        :param user (string): The user name.
        :param portnum (int): The number of exposed ports.
        :param specport (list of ints): The specified ports in random generated ports.

        return dckrinfo (dict), status (bool):
            dckrinfo:
                - user (string): The user name
                - sshport (int): The ssh connection port.
                - xport (list): The extra exposed ports.
                - ip (string): The connection ip address.
                - psd (string): The user password.
        """

        # Check if docker is existed
        conn = self.__connect()
        conn.exec_command(f"mkdir -p {os.path.dirname(self.dockerdb)}")
        i, o, e = conn.exec_command("hash docker 2>/dev/null && echo 1")
        output = o.readlines()
        lines = [l.strip('\n') for l in output]
        if len(lines) == 0:
            print("[x] Please install docker first!")
            conn.close()
            return None, False

        if specport is None: specport = list()

        dckrinfo = dict()
        dckrinfo['user'] = user
        dckrinfo['xport'] = list()

        # At least one port for ssh connection
        portnum += 1
        dckrinfo['ip'] = self.hostip

        # Check if the container exists
        if self.hasimage(user):
            print('[!] Docker for the user is existed!')
            return self.get_userinfo(user), True

        # Check port satisfication
        rndports, status = self.rndport(portnum, specport)
        if status is False:
            print("[x] Cannot listenning ports!")
            conn.close()
            return None, False
        dckrinfo['sshport'] = rndports[0]
        exposed_ports = " --publish {port:d}:22 ".format(port = rndports[0])
        for p in rndports[1:]:
            dckrinfo['xport'].append(p)
            exposed_ports += " --publish {port:d}:{port} ".format(port = p)

        # Determine if we shuold create the user
        if not self.is_user_exist(user): self.newuser(user)

        # Upload configuration file
        tm = str(time.time())
        sftp = conn.open_sftp()
        with sftp.file(f"/tmp/{tm}.sourcelist", "w") as _:
            _.write(sourcelist)
        with sftp.file(f"/tmp/{tm}.motd", "w") as _:
            _.write(motdfmt.format(user = user, hostid = self.hostid))
        with sftp.file(f"/tmp/{tm}.supervisord", "w") as _:
            _.write(sprvsrfile)
        with sftp.file(f"/tmp/{tm}.init", "w") as _:
            _.write(init)
        with sftp.file(f"/tmp/{tm}.dockerfile", "w") as _:
            dckr = dckrfmt.format(sourcelist = f"{tm}.sourcelist",
                    init = f"{tm}.init",
                    motd = f"{tm}.motd",
                    sprvsr = f"{tm}.supervisord",
                    user = f"{user}",
                    psdlen = 15)
            _.write(dckr)
        sftp.close()

        # docker build to build base image
        dckrbuild = "docker build --tag {hostid:s}:{user:s} --file {dckr:s} /tmp".format(
                hostid = self.hostid,
                user = user,
                dckr = f"/tmp/{tm}.dockerfile")
        print("[+] {}".format(dckrbuild))
        stdin, stdout, stderr = conn.exec_command(dckrbuild)
        err = stdout.channel.recv_exit_status()
        if err:
            print("[x] Cannot run docker build!")
            for line in stderr.readlines():
                print(line.strip('\n'))
            conn.close()
            return None, False

        # docker run to generate container
        dckrun = "docker run --hostname={hostid:s} --name {user:s} --volume /home/{user}:/home/{user}/share".format(
                hostid = self.hostid, user = user)
        dckrun += exposed_ports
        dckrun += " -d {hostid:s}:{user:s} ".format(hostid = self.hostid, user = user)
        print("[+] {}".format(dckrun))
        stdin, stdout, stderr = conn.exec_command(dckrun)
        err = stdout.channel.recv_exit_status()
        if err:
            print("[x] docker run failed!")
            conn.close()
            return None, False

        # docker exec to fix shared folder permission
        dckrperm = "docker exec -i {user:s} chown -R {user}:{user} /home/{user}/share".format(user = user)
        print("[+] {}".format(dckrperm))
        stdin, stdout, stderr = conn.exec_command(dckrperm)
        err = stdout.channel.recv_exit_status()
        if err:
            print("[x] Cannot change share folder permission!")
            conn.close()
            return None, False

        # docker exec to get default password
        i, o, e  = conn.exec_command(f"docker exec -i {user} cat /home/{user}/.defpsd")
        if o.channel.recv_exit_status():
            print("[x] Cannot retrieve default password!")
            print(f"[ERROR] {e.readlines()}")
            conn.close()
            return None, False
        else:
            lines = o.readlines()
            dckrinfo['psd'] = lines[0].strip('\n')

        # Remove unused files
        conn.exec_command(f'rm -rf /tmp/{tm}.*')

        # Save user information
        self.set_userinfo(user, dckrinfo)

        conn.close()
        return dckrinfo, True

    def set_userinfo(self, user, userinfo):
        conn = self.__connect()
        sftp = conn.open_sftp()

        userdb = dict()
        if self.is_file_exist(self.dockerdb):
            fuserdb = sftp.file(self.dockerdb, 'r')
            userdb.update(json.load(fuserdb))
            fuserdb.close()
        userdb[user] = userinfo
        fuserdb = sftp.file(self.dockerdb, 'w')
        json.dump(userdb, fuserdb)
        fuserdb.close()

        sftp.close()
        conn.close()

    def is_file_exist(self, path):
        conn = self.__connect()
        sftp = conn.open_sftp()
        status = True
        try:
            sftp.stat(path)
        except IOError:
            status = False
        sftp.close()
        conn.close()
        return status

    def get_userinfo(self, user = None):
        """Get one or all user hosted in the host"""
        conn = self.__connect()
        sftp = conn.open_sftp()
        if not self.is_file_exist(self.dockerdb): return None
        fuserdb = sftp.file(self.dockerdb, 'r')
        userdb = json.load(fuserdb)
        sftp.close()
        conn.close()
        if user is None:
            return userdb
        elif user in userdb.keys():
            return userdb[user]
        else:
            return None

    @staticmethod
    def getoutput(conn, cmd):
        i, o, e = conn.exec_command(cmd)
        err = o.channel.recv_exit_status()
        if err:
            return None, False
        else:
            output = o.readlines()
            lines = [l.strip('\n') for l in output]
            return lines, True

    def gethome(self):
        conn = self.__connect()
        # realpath command is not available in some ubuntu release
        homes, ok = self.getoutput(conn, 'readlink -f ~')
        home = None
        if ok: home = homes[0]
        conn.close()
        return home

    def change_passwd(self, newpasswd):
        pass

    def change_sshkey(self, key):
        """Change user ssh

        :key (str): The path to load or save ssh key.
        """

        conn = self.__connect()
        sftp = conn.open_sftp()
        home = self.gethome()
        haserr = False
        if home is not None:
            key = os.path.expanduser(key)
            if not os.path.exists(key):
                print('[x] Cannot find key in the given path!')
                haserr = True
            if not key.endswith('.pub'):
                print('[x] Not a public ssh key!')
                haserr = True
            if not haserr:
                with open(key, 'r') as fkey:
                    with sftp.file(f'{home}/.ssh/authorized_keys', 'w') as _:
                        _.write(fkey.read())
        else:
            print("[x] Cannot get home path!")
            haserr = True
        sftp.close()
        conn.close()
        return False if haserr else True

def add_sshkey_by_passwd(ip, user, passwd):
    pass

if __name__ == "__main__":
    pass
