import optparse, os, psutil, time, zlib
from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol
from twisted.protocols import basic
from twisted.python import log
from Crypto.Cipher import AES

class CommunicatorProtocol(Protocol):

    def dataReceived(self, data):

        splitdata = data.split("|||")
        label = splitdata[0]

        import sqlite3 as lite
        import sys

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

    def clientConnectionMade(self, client):
        self.client = client

    def send_message(self, msg):
        self.client.transport.write(msg + "\n")

class ListenerProtocol(Protocol):

    def dataReceived(self, data):
        self.factory.otherfactory.send_message(data)

class ListenerFactory(ServerFactory):

    protocol = ListenerProtocol

    def __init__(self, reactor, otherfactory):
        self.reactor = reactor
        self.otherfactory = otherfactory

def main():

    from twisted.internet import reactor

    factory = CommunicatorFactory(reactor)

    print "Starting reactor..."
    reactor.connectTCP("localhost", 231, factory)

    communicator_factory = ListenerFactory(reactor, factory)
    port = reactor.listenTCP(4334, communicator_factory,
                             interface="127.0.0.1")


    print 'Listening on %s.' % (port.getHost())

    reactor.run()

if __name__ == '__main__':
    main()
