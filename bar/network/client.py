import sys 
import optparse 
import sqlite3 as lite
from twisted.internet import reactor, protocol, task
from twisted.internet.endpoints import TCP4ClientEndpoint
from Crypto import Random
from Crypto.Cipher import AES

class BARClientProtocol(protocol.Protocol):

    def connectionLost(self, reason):
        reactor.stop()

    def connectionMade(self):
        self.factory.clientConnectionMade(self)

    def dataReceived(self, data):
        pass

class BARClientFactory(protocol.ClientFactory):
    protocol = BARClientProtocol
    def __init__(self, label, message, newlabel, sharedkey):
        self.label = label
        self.newlabel = newlabel
        self.message = message
        self.sharedkey = sharedkey
        self.bar_server = ""

    def announce(self):
        self.newlabel = genLbl()
        print "Sending..."
        self.bar_server.transport.write("BROADCAST " + str(self.label) + "|||" + self.AESencrypt(self.sharedkey, self.newlabel + "|||" + str(self.message)) + "|||\n")

    def AESencrypt(self, skey, m):
        '''
        Encrypt given message with shared key.
        '''
        iv = '\x00' * 16
        stream = AES.new(skey, AES.MODE_CFB, iv)
        con = lite.connect('bar/db/bar.db')
        with con:                
                cur = con.cursor() 
                cur.execute("UPDATE contacts SET label=? WHERE label=?", (str(self.newlabel), str(self.label)))
        self.label = self.newlabel
        if con:
            con.close()
        return stream.encrypt(m)

    def clientConnectionMade(self, server):
        self.bar_server = server
        self.announce()

def genLbl():
    '''
    Generate a new Label.
    '''
    rpool =  Random.new()
    Random.atfork() 
    return rpool.read(16).encode("hex")

def send_broadcast_message(contact, message):
    factory = BARClientFactory(contact[2], message, genLbl(), contact[4])
    reactor.connectTCP("localhost", 4333, factory)
    reactor.run()
