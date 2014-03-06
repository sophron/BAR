from twisted.internet import reactor, protocol, task
from twisted.internet.endpoints import TCP4ClientEndpoint
from Crypto import Random
from Crypto.Cipher import AES
import time, psutil, sys, optparse, sqlite3 as lite

class MyProtocol(protocol.Protocol):
    def connectionMade(self):
        self.factory.clientConnectionMade(self)

    def dataReceived(self, data):

        if data == "OK":
            print "Received a succesfull message from the server."

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
                pass


    def AESdecrypt(self, skey, c):
        '''
        Decrypt given message with shared key.
        '''

        iv = '\x00' * 16
        stream=AES.new(skey, AES.MODE_CFB, iv)
        return stream.decrypt(c)

class MyFactory(protocol.ClientFactory):
    protocol = MyProtocol
    def __init__(self, label, message, newlabel, sharedkey):
        self.label = label
        self.newlabel = newlabel
        self.message = message
        self.sharedkey = sharedkey
        self.start = ""
        self.clients = []

    def announce(self):

        self.newlabel = genLbl()

        for client in self.clients:

            print "Sending..."
            client.transport.write("BROADCAST " + str(self.label) + "|||" + self.AESencrypt(self.sharedkey, self.newlabel + "|||" + str(self.message)) + "|||\n")

        reactor.stop()

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

    def clientConnectionMade(self, client):
        self.clients.append(client)
        self.announce()

class LoginFactory(protocol.ClientFactory):
    protocol = MyProtocol
    def __init__(self):
        self.clients = []
        self.lc = task.LoopingCall(self.announce)
        self.lc.start(2)

    def announce(self):

        for client in self.clients:
            self.start = time.time()
            client.transport.write("LOGIN 4333\n")

    def clientConnectionMade(self, client):
        self.clients.append(client)
        self.announce()

def genLbl():
    '''
    Generate a new Label.
    '''

    rpool =  Random.new()
    Random.atfork() 
    return rpool.read(16).encode("hex")

def send_broadcast_message(contact, message):

    factory = MyFactory(contact[2], message, genLbl(), contact[4])
    reactor.connectTCP("localhost", 231, factory)
    reactor.run()

def login_to_bar():

    factory = LoginFactory()
    reactor.connectTCP("localhost", 231, factory)
    reactor.run()

