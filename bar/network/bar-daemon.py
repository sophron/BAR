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
from bar.common.message import Message
import bar.common.label as label
import bar.common.aes as aes
import bar.common.db as db

HIDDEN_CLIENT = 1
HIDDEN_SERVICE = 0
HIDDEN_SERVICE_PORT = 80

class CommunicatorProtocol(NetstringReceiver):

    operations = ["welcome", "ok", "broadcast"]

    def caller(self, func, args):
        return getattr(self, func)(args) 

    def check_welcome(self, data):
        if "BAR" in data:
            return 1

    def received_welcome(self, data):
        print "Received welcome messsage from the BAR server."

    def check_ok(self, data):
        if data[:2] == "OK":
            return 1

    def received_ok(self, data):
        print "Received OK message from the BAR server."

    def check_broadcast(self, data):
        return 1

    def received_broadcast(self, data):
            message = Message(data)
            row = db.select_entry("label", message.label)
            message.decrypt(row[4])
            if not message.validate():
                print "Received an invalid message."
                return
            if HIDDEN_CLIENT:
                if self.factory.listener_factory:
                    self.factory.listener_factory.send_message(message.cleartext_msg)
                    self.factory.listener_factory.client.transport.loseConnection()
                    db.update_entry("label", message.label, "label", message.new_label)
            if HIDDEN_SERVICE:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(('localhost', HIDDEN_SERVICE_PORT))
                s.send(message.cleartext_msg)
                data = s.recv(2048)
                s.close()
                more_new_label = label.gen_lbl()
                db.update_entry("label", retr_label, "label", more_new_label)
                self.factory.transmitDataBackToClient(message.new_label, row[4], more_new_label, data)

    def stringReceived(self, data):
        for op in self.operations:
            if self.caller("check_" + op, data):
                self.caller("received_" + op, data)
                return

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
        self.send_message("BROADCAST " + str(label) + "|||" + aes.aes_encrypt(sharedkey, str(label) + "|||" + str(newlabel) + "|||" + str(message)))

class ListenerProtocol(NetstringReceiver):

    def dataReceived(self, data):
        host = re.findall(r"Host: (?P<value>.*?)\r\n", data)[0]
        contact = db.select_entry("name", host)
        newlabel = label.gen_lbl()
        if contact:
            self.factory.communicator_factory.transmitDataBackToClient(contact[2], contact[4], newlabel, data)
            db.update_entry("label", contact[2], "label", newlabel)

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
    reactor.connectTCP("192.168.1.2", 231, communicator_factory)
    port = reactor.listenTCP(4333, listener_factory,
                             interface="127.0.0.1")
    print 'Listening on %s.' % (port.getHost())
    reactor.run()

if __name__ == '__main__':
    main()
