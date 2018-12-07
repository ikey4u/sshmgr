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

# demo output

    ➜  sshmgr (master) ✗ python sshmgr.py 108 -u Tom -x newdckr
    [+] docker build --tag 108:Tom --file /tmp/1544153926.821344.dockerfile /tmp
    [+] docker run --hostname=108 --name Tom --volume /home/Tom:/home/Tom/share --publish 25826:22  --publish 7171:7171  --publish 50543:50543  --publish 19085:19085  -d 108:Tom
    [+] docker exec -i Tom chown -R Tom:Tom /home/Tom/share
    Now you can use 'ssh Tom@210.75.xxx.xx -p xxx' and password 'xxxxxxxxxxx' to login.
    Your extra available ports are: xxxx,xxx,xxx

