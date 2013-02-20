import socket
import yaml
import sys
import pyinotify

class DNSQuery:
    def __init__(self, data, config = None):
        self.data=data
        self.dominio=''
        if config:
            self.config = config
        else:
            print "FATAL! Required configuration"
            sys.exit(-1)

        tipo = (ord(data[2]) >> 3) & 15   # Opcode bits
        if tipo == 0:                     # Standard query
            ini=12
            lon=ord(data[ini])
            while lon != 0:
                self.dominio+=data[ini+1:ini+lon+1]+'.'
                ini+=lon+1
                lon=ord(data[ini])

    def risposta(self):
        packet = ''
        packet += self.data[:2] + "\x81\x80"
        packet += self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'
        packet += self.data[12:]
        packet += '\xc0\x0c'
        packet += '\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'
        ip = self.config.resolve(self.dominio[:-1])
        packet += str.join('', map(lambda x: chr(int(x)), ip.split('.')))
        return packet, ip

class Configuration(pyinotify.ProcessEvent):
    def __init__(self, configFile = "dnspython.yaml"):
        self.configFile = configFile
        self.config = {}
        self.__load_config()
        self.watchManager = pyinotify.WatchManager()
        self.notifier = pyinotify.ThreadedNotifier(self.watchManager, self)
        self.watchManager.add_watch(self.configFile, pyinotify.IN_CLOSE_WRITE)
        self.notifier.start()

    def stop(self):
        self.notifier.stop()

    def __load_config(self):
        try:
            self.config = yaml.load(open(self.configFile).read())
            print "Reloaded config!"
        except IOError as e:
            print "The file %s does not seem to exists, aborting" % self.configFile
            sys.exit(-1)
        except yaml.ScannerError as e:
            print "File %s contained errors, please check your syntax" % self.configFile
            sys.exit(-1)
        except Exception as e:
            print "ERROR: %s" % e.message
            sys.exit(-1)
        print "loaded config:", self.config

    def process_IN_CLOSE_WRITE(self, event):
        self.__load_config()

    def resolve(self, name):
        if name in self.config:
            return self.config[name]
        else:
            try:
                return socket.gethostbyname_ex(name)[2][0]
            except socket.gaierror:
                return "0.0.0.0"


if __name__ == '__main__':

    config = Configuration()

    udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udps.bind(('',53))

    try:
        while True:
            data, addr = udps.recvfrom(1024)
            p = DNSQuery(data, config)
            packet, final_ip = p.risposta()
            udps.sendto(packet, addr)
            print 'Risposta: %s -> %s' % (p.dominio, final_ip)
    except KeyboardInterrupt as e:
        print "Quit"
        udps.close()

    config.stop()

