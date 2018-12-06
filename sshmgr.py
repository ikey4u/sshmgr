#! /usr/bin/env python3
#! -*- coding:utf-8 -*-

import paramiko
import os
import sys
import random
import time
import json
import argparse

dckrfmt = """
FROM ubuntu:16.04
SHELL ["/bin/bash", "-c"]
RUN apt update && apt install -y wget ca-certificates apt-transport-https && \
    wget http://ahageek.com/txt/16.04.txt -O - | grep -v @ > /etc/apt/sources.list && apt update && \
    mkdir -p /root/.ssh/ && mkdir -p /var/run/sshd && mkdir -p /var/log/supervisor && \
    apt install -y openssh-server vim git supervisor pwgen sudo locales && \
    useradd -d /home/{user:s} -m -s /bin/bash {user} && \
    usermod -aG sudo {user} && \
    echo "{user}@{hostid:s}" > /home/{user}/.userid && \
    rm -rf /etc/update-motd.d/* && \
    echo '#! /bin/bash' > /etc/update-motd.d/00-header-hpdmlabs && \
    echo "echo ----------------------------------" >> /etc/update-motd.d/00-header-hpdmlabs && \
    echo "echo Welcome {user} to HPDM Labs!" >> /etc/update-motd.d/00-header-hpdmlabs && \
    echo "echo ID   : \$(cat /home/{user}/.userid)" >> /etc/update-motd.d/00-header-hpdmlabs && \
    echo "echo ----------------------------------" >> /etc/update-motd.d/00-header-hpdmlabs && \
    chmod +x /etc/update-motd.d/00-header-hpdmlabs && \
    echo "LC_ALL=en_US.UTF-8" >> /etc/environment && \
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen  && \
    echo "LANG=en_US.UTF-8" > /etc/locale.conf  && \
    locale-gen en_US.UTF-8 && \
    psd=$(pwgen -N 1 {psdlen:d}) && echo "{user}:$psd" | chpasswd && echo $psd > /home/{user}/.defpsd && \
        printf "\\n{spy:s}$(cat /home/{user}/.defpsd){spy}\\n"
COPY {supervisord:s} /etc/supervisor/conf.d/supervisord.conf
ENTRYPOINT "/usr/bin/supervisord"
"""

sprvsrfile = """
[supervisord]
nodaemon=true
[program:sshd]
command=/usr/sbin/sshd -D
"""

class SSH:
    def __init__(self, hostid):
        self.hostid = hostid
        self.hostip = ""
        self.dockerdb = "/root/dockerdb/userdb.json"

        try:
            conn = self.__connect()
            conn.exec_command(f"mkdir -p {os.path.dirname(self.dockerdb)}")
            i, o, e = conn.exec_command("hash docker 2>/dev/null && echo 1")
            lines = [l.strip('\n') for l in o.readlines()]
            if len(lines) == 0:
                print("[x] Please install docker first!")
                conn.close()
                raise
            else:
                conn.close()
        except Exception as e:
            print(f"[x] Error happened when connect to {hostid}!")
            sys.exit(1)

    def __connect(self):
        config = paramiko.SSHConfig()
        with open(os.path.expanduser('~/.ssh/config')) as _:
            config.parse(_)
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
                conn.exec_command(f"docker stop {jar}")
                conn.exec_command(f"docker rm {jar}")
            conn.exec_command(f"docker rmi {self.hostid}:{user}")
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
        conn.exec_command("docker image prune")
        conn.exec_command("docker contanier prune")
        conn.close()

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

        if specport is None: specport = list()

        dckrinfo = dict()
        dckrinfo['user'] = user
        dckrinfo['xport'] = list()

        # At least one port for ssh connection
        portnum += 1
        conn = self.__connect()
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
        # write supervisord file
        sprvsr = "/tmp/" + tm + ".supervisord"
        fsprvsr = sftp.file(sprvsr, 'w')
        fsprvsr.write(sprvsrfile)
        fsprvsr.close()
        # write dockerfile
        spy = "[DOCKER]"
        dckrfile = dckrfmt.format(user = user,
                hostid = self.hostid,
                supervisord = tm + ".supervisord", # shuold use relative path
                spy = spy,
                psdlen = 15)
        dckr = '/tmp/' + tm + '.dockerfile'
        fdckr = sftp.file(dckr, 'w')
        fdckr.write(dckrfile)
        fdckr.close()

        sftp.close()

        # docker build to build base image
        dckrbuild = "docker build --tag {hostid:s}:{user:s} --file {dckr:s} /tmp".format(
                hostid = self.hostid,
                user = user,
                dckr = dckr)
        print("[+] {}".format(dckrbuild))
        stdin, stdout, stderr = conn.exec_command(dckrbuild)
        err = stdout.channel.recv_exit_status()
        if err:
            print("[x] Cannot run docker build!")
            for line in stdout.readlines():
                print(line.strip('\n'))
            conn.close()
            return None, False
        else:
            lines = stdout.readlines()
            for line in lines:
                line = line.strip('\n').strip()
                if line.startswith(spy):
                    dckrinfo['psd'] = line.strip(spy)
                    break

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
            print("[x] docker exec failed!")
            conn.close()
            return None, False

        # Remove unused files
        conn.exec_command(f'rm -rf {sprvsr}')
        conn.exec_command('rm -rf {dckr}')

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

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "A powerful linux server manager")
    parser.add_argument("hostid", help = "The ssh host ID", type = str)
    parser.add_argument("-u", "--user", help = "The user name", type = str)
    parser.add_argument("-x", choices = ["newdckr", "deldckr", "getinfo"],
            help = "The action to execture", type = str)
    args = parser.parse_args()

    ssh = SSH(args.hostid)

    if args.user:
        if args.x == "newdckr":
            dckrinfo, ok = ssh.newdckr(args.user, 3)
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
            ssh.deldckr(args.user)
        elif args.x == "getinfo":
            ssh.get_userinfo(args.user)
        else:
            print("[x] Unknown action!")
    else:
        users = ssh.get_userinfo()
        for user in users:
            print(user)

