# This is the Twisted Fast Poetry Server, version 1.0

import optparse, os, psutil, time, socket

from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol
from twisted.protocols import basic

clients = []

def parse_args():

    parser = optparse.OptionParser()

    help = "The port to listen on. Default to a random available port."
    parser.add_option('--port', type='int', help=help)

    help = "The interface to listen on. Default is localhost."
    parser.add_option('--iface', help=help, default='localhost')

    options, args = parser.parse_args()

    return options


class PoetryProtocol(Protocol):

    def connectionMade(self):
        clients.append(self)

    def dataReceived(self, data):

        if data[:5] == "LOGIN":

            port = data.split()

            if len(port) <= 1:
                self.transport.write("Ok, but what's the port?")
            else:
                port = int(port[1])
                ip = str(self.transport.getPeer().host)
                import sqlite3 as lite
                import sys

                con = lite.connect('bar/db/bar.db')

                with con: 
                    cur = con.cursor() 
                    cur.execute("INSERT INTO clients(ip, port) VALUES(?, ?);", (ip, port))
                
            self.transport.write("OK")

        elif data[:9] == "BROADCAST":

            if len(data) <= 11:
                self.transport.write("Ok, but where's the message to broadcast?")
            else:

                message = data[10:]

                for client in clients:
                    client.transport.write(message)

                self.transport.write("OK")
 
        else:
            self.transport.write("I can break rules too.")
            self.transport.write("Given command:" + data)

class PoetryFactory(ServerFactory):

    protocol = PoetryProtocol

    def __init__(self, reactor):
        self.reactor = reactor

class BarClientProtocol(basic.LineReceiver):

    def connectionMade(self):
        self.transport.write(self.factory.message)

class BarClientFactory(ServerFactory):

    protocol = BarClientProtocol

    def __init__(self, reactor, message):
        self.message = message
        self.reactor = reactor

    def startedConnecting(self, connector):
        print self, connector
        pass

    def clientConnectionFailed(self, connector, reason):
        pass

    def clientConnectionLost(self, connector, reason):
        pass

def main():
    options = parse_args()

    from twisted.internet import reactor

    factory = PoetryFactory(reactor)

    port = reactor.listenTCP(options.port or 231, factory,
                             interface=socket.gethostbyaddr(socket.gethostbyname(socket.gethostname()))[2][0])

    print 'Serving on %s.' % (port.getHost())
    reactor.run()


if __name__ == '__main__':
    main()
