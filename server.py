#!/usr/bin/env python

import socket
from threading import Thread
import logging
from dns import message, query, rrset, rdataclass, rdatatype
import sys
import time
import signal
import yaml
import os

logging.basicConfig(filename = "log", level = logging.DEBUG)

class DnsServer(Thread):
    def __init__(self, handler):
        # Init the thread
        Thread.__init__(self)

        self.dostop = False
        if not handler:
            raise NotImplemented("Need to receive an handler class for the server!")

        self.handler = handler
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.handler.getHost(),self.handler.getPort()))

    def run(self):
        logging.info("Server running")
        while not self.dostop:
            data, addr = self.socket.recvfrom(1024)
            response = self.handle(data, addr)
            self.socket.sendto(response.to_wire(), addr)
        self.socket.close()

    def stop(self):
        self.dostop = True

    def handle(self, data, addr):
        return self.handler.handle(data, addr)

class Handler(object):
    def __init__(self, configFile = 'dnspython.yaml'):
        signal.signal(signal.SIGUSR1, self.signal_handler)
        self.configFile = configFile
        self.config = {}
        self.__load_config()

    def signal_handler(self, signun, frame):
        logging.info("Got signal, reloading current configuration")
        self.__load_config()

    def getHost(self):
        return self.config['general']['host']

    def getPort(self):
        return self.config['general']['port']

    def __load_config(self):
        try:
            del self.config
            self.config = yaml.load(open(self.configFile).read())
        except IOError as e:
            print "The file %s does not seem to exists, aborting" % self.configFile
            sys.exit(-1)
        except yaml.scanner.ScannerError as e:
            print "File %s contained errors, please check your syntax" % self.configFile
            sys.exit(-1)
        except Exception as e:
            print "ERROR: %s" % e.message
            sys.exit(-1)
        logging.info("Loaded new configuration: %s" % self.config)

    def _name_from_message(self, request):
        for each in request.question:
            name = each.name.to_text()[:-1]
            logging.info("Extracted %s from request" % str(name))
            return name

    def _make_response_for(self, request, name, address):
        response = message.make_response(request)
        respset = rrset.from_text(name + ".", 300, rdataclass.IN, rdatatype.A, address)
        response.answer.append(respset)
        return response

    def handle(self, data, addr):
        logging.info("Handling request for %s" % str(addr))
        request = message.from_wire(data)
        name = self._name_from_message(request)
        if name in self.config['mapping']:
            logging.debug("Found %s in config file" % name)
            return self._make_response_for(request, name, self.config['mapping'][name])
        else:
            logging.debug("Resolved %s from real dns" % name)
            return query.udp(request, self.config['general']['nameserver'])

def clean_pid(pidfile):
    try:
        os.remove(pidfile)
    except OSError:
        pass

if __name__ == "__main__":
    pid = os.getpid()
    pidfile = "dnspython.pid"
    logging.info("Starting as pid %s" % pid)
    try:
        open(pidfile,"w+").write(str(pid))
    except Exception as e:
        print e.message
        print "FATAL: could not open the pidfile %s" % pidfile
    try:
        handler = Handler()
        server = DnsServer(handler)
        logging.info("Launching thread")
        server.daemon = True
        server.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        clean_pid(pidfile)
        sys.exit(0)
    server.join()
    clean_pid(pidfile)
    logging.info("Quitting")
