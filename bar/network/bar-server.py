import os
import psutil
import time
import socket
import sys
import sqlite3 as lite
from twisted.internet import defer, reactor
from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol
from twisted.protocols import basic

clients = []

class BARServerProtocol(Protocol):

    def connectionMade(self):
        clients.append(self)
        self.transport.write("=== BAR Server ===\n")

    def dataReceived(self, data):
        if data[:9] == "BROADCAST":
            self.broadcast(data)
        elif data[:4] == "QUIT":    
            self.close_connection()
        else:
            self.transport.write("I can break rules too.\n")

    def broadcast(self, data):
        if len(data) <= 11:
            self.transport.write("Ok, but where's the message to broadcast?\n")
        else:
            message = data[10:]
            for client in clients:
                client.transport.write(message)
            self.transport.write("OK\n")

    def close_connection(self):
        self.transport.loseConnection()
 
    def connectionLost(self, reason):
        clients.remove(self)

class BARServerFactory(ServerFactory):
    protocol = BARServerProtocol

    def __init__(self):
        pass

def main():
    factory = BARServerFactory()
    port = reactor.listenTCP(231, factory,
                             #interface=socket.gethostbyaddr(socket.gethostbyname(socket.gethostname()))[2][0])
                            interface='localhost')
    print 'Serving on %s.' % (port.getHost())
    reactor.run()

if __name__ == '__main__':
    main()
