#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os 
import time
import zlib
import sys
import re
import socket
import sqlite3 as lite
from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol
from twisted.protocols.basic import LineReceiver, NetstringReceiver
from twisted.protocols import basic
from twisted.web import proxy, http
from twisted.python import log
from twisted.internet import reactor
from bar.common.message import Message
import bar.common.label as label
import bar.common.aes as aes
from bar.common.db import Bardb

db = Bardb()

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
            print "Received feed."
            message = Message(data)
            row = db.select_entries("contacts", {"label": message.label})
            if len(row) == 0:
                print "Can't find this label: " + message.label
                return
            row = row[0]
            message.decrypt(row["sharedkey"])
            if not message.validate():
                print "Received an invalid message."
                return
            print "Found label: " + message.label
            if self.factory.role == "hidden-client":
                if self.factory.listener_factory:
                    self.factory.listener_factory.send_message(message.cleartext_msg)
                    self.factory.listener_factory.client.transport.loseConnection()
                    db.insert_entry("contacts", {"name": self.factory.name, "label":message.new_label, "sharedkey": row["sharedkey"]})
            else:
                if self.factory.role == "proxy":
                    message.cleartext_msg = re.sub(r'CONNECT (?P<value>.*?) HTTP/1.0\r\n', 'CONNECT localhost HTTP/1.0\r\n', message.cleartext_msg)
                socks_client_factory = HTTPClientFactory(reactor, message)
                socks_client_factory.set_communicator(self)
                reactor.connectTCP("localhost", 4333, socks_client_factory)
                db.insert_entry("contacts", {"name": self.factory.name, "label":message.new_label, "sharedkey": row["sharedkey"]})

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

    def __init__(self, reactor, name, role):
        self.reactor = reactor
        self.name = name
        self.role = role

    def set_listener(self, listener_factory):
        self.listener_factory = listener_factory

    def clientConnectionMade(self, client):
        self.client = client

    def send_message(self, msg):
        print "Sending..."
        self.client.sendString(msg)

    def send_broadcast_request(self, label, sharedkey, newlabel, message):
        self.send_message("BROADCAST " + str(label) + "|||" \
                         + aes.aes_encrypt(sharedkey, str(label) \
                         + "|||" + str(newlabel) \
                         + "|||" + str(message)))

class ListenerProtocol(Protocol):

    def dataReceived(self, data):
        contact = db.select_entries("contacts", {"name": self.factory.communicator_factory.name})
        if len(contact) == 0:
            return
        contact = contact[0]
        newlabel = label.gen_lbl()
        if contact:
            self.factory.communicator_factory.send_broadcast_request(contact['label'], contact['sharedkey'], newlabel, data)
        return

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

class HTTPClientProtocol(Protocol):

    def dataReceived(self, data):
        contact = db.select_entries("contacts", {"name": self.factory.communicator_factory.factory.name})
        if len(contact) == 0:
            return
        contact = contact[0]
        more_new_label = label.gen_lbl()
        self.factory.communicator_factory.factory.send_broadcast_request(self.factory.message.label, contact['sharedkey'], more_new_label, data)

    def connectionMade(self):
        self.factory.clientConnectionMade(self)

class HTTPClientFactory(ClientFactory):
    protocol = HTTPClientProtocol

    def __init__(self, reactor, message):
        self.reactor = reactor
        self.message = message

    def clientConnectionMade(self, client):
        self.client = client
        self.client.transport.write(self.message.cleartext_msg)

    def set_communicator(self, communicator_factory):
        self.communicator_factory = communicator_factory

class ProxyFactory(http.HTTPFactory):
	protocol = proxy.Proxy

def daemon_main(name, role, server):

    #parser = argparse.ArgumentParser(description='bar-daemon')
    #parser.add_argument('--name', default=False, help='Label of contact')
    #parser.add_argument('--role', default=False, help='Role of client')
    #args = parser.parse_args()
    
    #name = name or args.name
    #role = role or args.role    

    communicator_factory = CommunicatorFactory(reactor, name, role)
    if role == "hidden-client": 
        listener_factory = ListenerFactory(reactor, communicator_factory)
        communicator_factory.set_listener(listener_factory)
        port = reactor.listenTCP(4333, listener_factory,
                                 interface="127.0.0.1")
    else:
        port = reactor.listenTCP(4333, ProxyFactory())

    print "Starting reactor..."
    reactor.connectTCP(server, 231, communicator_factory)
    print 'Listening on %s.' % (port.getHost())
    reactor.run()

if __name__ == '__main__':
    daemon_main("foo", "hidden-client")
