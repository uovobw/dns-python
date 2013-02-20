#!/usr/bin/env python

import socket
from threading import Thread
import logging
from dns import message
import sys
import time

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
        self.socket.bind(('',53))

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
    def __init__(self):
        pass

    def handle(self, data, addr):
        logging.info("Handling request for %s" % str(addr))
        request = message.from_wire(data)
        logging.info("Request: %s" % str(request))
        return message.make_response(request)

if __name__ == "__main__":
    logging.info("Starting")
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
        sys.exit(0)
    server.join()
    logging.info("Quitting")
