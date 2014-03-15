import optparse
import os 
import psutil
import time
import zlib
import sys
import sqlite3 as lite
from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol
from twisted.protocols import basic
from twisted.python import log
from twisted.internet import reactor
from Crypto.Cipher import AES

class CommunicatorProtocol(Protocol):

    def dataReceived(self, data):
        if data[:2] == "OK":
            print "Received a succesfull message from the server."
            self.factory.listener_factory.send_message(data)
        splitdata = data.split("|||")
        label = splitdata[0]
        con = lite.connect('bar/db/bar.db')
        with con:
            cur = con.cursor() 
            cur.execute("SELECT * FROM contacts WHERE label=:label", {"label":label})
            row = cur.fetchone()
            if row != None:
                start = time.time()
                encrypted = splitdata[1]
                cleartext = self.AESdecrypt(row[4], encrypted)
                newlabel = cleartext.split("|||")[0]
                cur.execute("INSERT INTO messages(message) VALUES(?);", (cleartext.split("|||")[1].decode('ascii'),))
                cur.execute("UPDATE contacts SET label=? WHERE label=?", (newlabel, label))
            else:
                print "Couldn't find the retrieved label. Rejecting the message."

    def AESdecrypt(self, skey, c):
        '''
        Decrypt given message with shared key.
        '''
        iv = '\x00' * 16
        stream=AES.new(skey, AES.MODE_CFB, iv)
        return stream.decrypt(c)

    def connectionMade(self):
        self.factory.clientConnectionMade(self)

class CommunicatorFactory(ClientFactory):
    protocol = CommunicatorProtocol

    def __init__(self, reactor):
        self.reactor = reactor

    def set_listener(self, listener_factory):
        self.listener_factory = listener_factory

    def clientConnectionMade(self, client):
        self.client = client

    def send_message(self, msg):
        self.client.transport.write(msg + "\n")

class ListenerProtocol(Protocol):

    def dataReceived(self, data):
        self.factory.communicator_factory.send_message(data)
        self.transport.loseConnection()

    def connectionMade(self):
        self.factory.clientConnectionMade(self)

class ListenerFactory(ServerFactory):
    protocol = ListenerProtocol

    def __init__(self, reactor, communicator_factory):
        self.reactor = reactor
        self.communicator_factory = communicator_factory

    def clientConnectionMade(self, client):
        self.client = client

    def send_message(self, msg):
        self.client.transport.write(msg + "\n")

def main():
    communicator_factory = CommunicatorFactory(reactor)
    listener_factory = ListenerFactory(reactor, communicator_factory)
    communicator_factory.set_listener(listener_factory)
    print "Starting reactor..."
    reactor.connectTCP("localhost", 231, communicator_factory)
    port = reactor.listenTCP(4333, listener_factory,
                             interface="127.0.0.1")
    print 'Listening on %s.' % (port.getHost())
    reactor.run()

if __name__ == '__main__':
    main()
