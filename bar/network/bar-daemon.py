import optparse
import os 
import psutil
import time
import zlib
import sys
import re
import socket
import sqlite3 as lite
from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol
from twisted.protocols.basic import LineReceiver, NetstringReceiver
from twisted.protocols import basic
from twisted.python import log
from twisted.internet import reactor
from bar.pybar import send_message
import bar.common.label as label
import bar.common.aes as aes

HIDDEN_CLIENT = 1
HIDDEN_SERVICE = 0
HIDDEN_SERVICE_PORT = 80

class CommunicatorProtocol(NetstringReceiver):

    def stringReceived(self, data):
        if data[:2] == "OK":
            print "Received a succesfull message from the server."
            return

        splitdata = data.split("|||")
        retr_label = splitdata[0]
        con = lite.connect('bar/db/bar.db')
        with con:
            cur = con.cursor() 
            cur.execute("SELECT * FROM contacts WHERE label=:label", {"label":retr_label})
            row = cur.fetchone()
            if not "BAR" in data: #FIXME
                if not row:
                    print "Couldn't find the retrieved label. Rejecting the message."
                    return
                start = time.time()
                encrypted = splitdata[1]
                cleartext = aes.aes_decrypt(row[4], encrypted)
                newlabel = cleartext.split("|||")[0]
                message = cleartext.split("|||")[1]

                if HIDDEN_CLIENT:
                    if self.factory.listener_factory:
                        self.factory.listener_factory.send_message(message)
                        self.factory.listener_factory.client.transport.loseConnection()
                    cur.execute("UPDATE contacts SET label=? WHERE label=?", (newlabel, retr_label))

                if HIDDEN_SERVICE:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect(('localhost', HIDDEN_SERVICE_PORT))
                    s.send(message)
                    data = s.recv(2048)
                    s.close()
                    more_new_label = label.gen_lbl()
                    cur.execute("UPDATE contacts SET label=? WHERE label=?", (more_new_label, retr_label))
                    self.factory.transmitDataBackToClient(newlabel, row[4], more_new_label, data)

    def connectionMade(self):
        print "Succeed."
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
        print "Sending..."
        self.client.sendString(msg)

    def transmitDataBackToClient(self, label, sharedkey, newlabel, message):
        self.send_message("BROADCAST " + str(label) + "|||" + aes.aes_encrypt(sharedkey, str(newlabel) + "|||" + str(message)) + "|||")


class ListenerProtocol(NetstringReceiver):

    def dataReceived(self, data):

        host = re.findall(r"Host: (?P<value>.*?)\r\n", data)[0]
        con = lite.connect('bar/db/bar.db')
        with con:
            cur = con.cursor() 
            cur.execute("SELECT * FROM contacts WHERE name=:name", {"name": host})
            contact = cur.fetchone() 

        newlabel = label.gen_lbl()

        if contact:
            self.factory.communicator_factory.transmitDataBackToClient(contact[2], contact[4], newlabel, data)

            with con:
                cur = con.cursor() 
                cur.execute("UPDATE contacts SET label=? WHERE label=?", (newlabel, contact[2]))
        
        if con:
            con.close()

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
        self.client.transport.write(msg)

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
