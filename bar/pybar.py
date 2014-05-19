#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, argparse, subprocess, signal
import sqlite3 as lite
from Crypto import Random
from bar.network.client import send_broadcast_message
from bar.network.bar_daemon import daemon_main

def parse_cli():
    '''
    The top-level parser is called "operation". Each subparser after it *must*
    have the suffix of the upper parser for the dest attribute.
    '''

    # Create the top-level parser.
    parser = argparse.ArgumentParser(description='py-bar: A BAR cli interface written in Python')
    subparsers = parser.add_subparsers(help='sub-command help', dest='operation')

    # Create the parser for the "contacts" command.
    contacts_parser = subparsers.add_parser('contacts', help='Subparser for managing contacts.')
    messages_parser = subparsers.add_parser('messages', help='Subparser for messages.')
    server_parser = subparsers.add_parser('server', help='Subparser for a BAR server.')
    login_parser = subparsers.add_parser('login', help='Subparser for logging in to a BAR server.')
    logout_parser = subparsers.add_parser('logout', help='Subparser for logging out from the BAR server.')

    login_parser.add_argument('--name', default=False, help='Name of contact')
    login_parser.add_argument('--role', default=False, help='Role of BAR client')

    subparsers = server_parser.add_subparsers(help='sub-command help', dest='server_operation')

    # Create the parser for the "server start" command.
    startserver_parser = subparsers.add_parser('start', help='Subparser for starting a server.')

    # Create the parser for the "server stop" command.
    stopserver_parser = subparsers.add_parser('stop', help='Subparser for stopping a server.')

    subparsers = contacts_parser.add_subparsers(help='sub-command help', dest='contacts_operation')

    # Create the parser for the "contacts add" command.
    addcontacts_parser = subparsers.add_parser('add', help='Subparser for adding contacts.')
    addcontacts_parser.add_argument('--name', default=False, help='Delete an existing contact.')
    addcontacts_parser.add_argument('--label', default=False, help='Delete an existing contact.')
    addcontacts_parser.add_argument('--sharedkey', default=False, help='Delete an existing contact.')

    # Create the parser for the "contacts delete" command.
    addcontacts_parser = subparsers.add_parser('delete', help='Subparser for adding contacts.')
    addcontacts_parser.add_argument('--name', default=False, help='Delete an existing contact.')

    # Create the parser for the "contacts show" command.
    showcontacts_parser = subparsers.add_parser('show', help='Subparser for adding contacts.')

    subparsers = messages_parser.add_subparsers(help='sub-command help', dest='messages_operation')

    # Arguments for "messages new" command.
    newmessages_parser = subparsers.add_parser('new', help='Subparser for sending a message.')
    newmessages_parser.add_argument('--name', default=False, help='Name of contact.')
    newmessages_parser.add_argument('--label', default=False, help='Label of contact.')
    newmessages_parser.add_argument('--body', default=False, help='Body of the message.')

    showmessages_parser = subparsers.add_parser('show', help='Subparser for sending a message.')

    return parser

def start_process(path, args):
    '''
    Runs a background process (daemon).
    '''

    daemon = subprocess.Popen([sys.executable, path, "--name", args.name, "--role", args.role])#, 
                                #stdout=subprocess.PIPE, 
                                #stderr=subprocess.STDOUT)

    return daemon.pid

def stop_process(process_name):
    '''
    Stops a background process (daemon).
    '''

    proc = subprocess.Popen(["pgrep", "-f", process_name], stdout=subprocess.PIPE) 

    # Kill process.
    for pid in proc.stdout:
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError as ex:
           continue

def start_server(args):
    '''
    Starts BAR server.
    '''

    if os.getuid() != 0:
        print "You need to be root to start the server. Aborting..."
        return

    print "Starting server..."

    server_pid = start_process("bar/network/bar-server.py")
    if server_pid:
        print "Bar server started."

def stop_server(args):
    '''
    Stops BAR server.
    '''

    if os.getuid() != 0:
        print "You need to be root to stop the server. Aborting..."
        return

    print "Stopping server..."
    stop_process("bar-server.py")
    print "Bar server stopped."

def login(args):
    '''
    Login to BAR server.
    '''

    if not args.name:
        print "You need to specify a name with --name."
        return

    if args.role not in ("hidden-service", "hidden-client", "proxy"):
        print "role has to be either 'hidden-service' or 'hidden-client' or 'proxy'"
        return

    print "Starting daemon..."
    
    daemon_main(args.name, args.role)

    #pid = start_process("bar/network/bar-daemon.py", args)
    #if pid:
    #    print "Daemon started with pid " + str(pid) + "."

def logout(args):
    '''
    Logout from BAR server.
    '''

    print "Stoping daemon..."
    stop_process("bar-daemon")
    print "Daemon stopped."


def show_messages(args):
    '''
    Shows all messages.
    '''

    con = lite.connect('bar/db/bar.db')
    with con:
        cur = con.cursor() 
        cur.execute("SELECT * FROM messages")
        rows = cur.fetchall()
        if rows:
            print "Messages\n--------"
            for row in rows:
                print row[1]
        else:
            print "There are no messages!"
    return


def send_message(args):
    '''
    Sends a message.
    '''

    if not args.name and not args.label:
        print "Please specify contact's name or label with --name or --label option. Aborting..."
        return
    if not args.body:
        print "Please specify the message to send with --body argument. Aborting..."
        return

    con = lite.connect('bar/db/bar.db')
    with con:
        cur = con.cursor() 
        if args.name and not args.label:
            cur.execute("SELECT * FROM contacts WHERE name=:name", {"name": args.name})
        elif not args.name and args.label:
            cur.execute("SELECT * FROM contacts WHERE label=:label", {"label": args.label})
        else:
            cur.execute("SELECT * FROM contacts WHERE name=:name AND label=:label", 
                        {"name": args.name, "label": args.label})
        contact = cur.fetchone() 
    if con:
        con.close()
    if contact == None:
        print "No contact found. Aborting..."
        return

    send_broadcast_message(contact, args.body)
    return
        

def gen_key():
    '''
    Generates a new label or shared key.
    '''

    rpool =  Random.new()
    Random.atfork() 
    return rpool.read(16).encode("hex")

def add_contact(args):
    '''
    Adds a new contact to the address book.
    '''

    if not args.name:
        print "Please specify contact's name with --name option. Aborting..."
        return
    if not args.label:
        answer = raw_input("No label was specified with --label option. \
        Do you want to create one now? [y/N] ")
        if answer in ("y","Y","yes","YES", "Yes"):
            args.label = gen_key()
    if not args.sharedkey:
        anwer = raw_input("No shared key was specified with --sharedkey option. \
        Do you want to create one now? [y/N] ")
        if answer in ("y","Y","yes","YES", "Yes"):
            args.sharedkey = gen_key()
    if not args.sharedkey or not args.label:
        print "Aborting..."
        return

    con = lite.connect('bar/db/bar.db')
    with con:
        cur = con.cursor() 
        cur.execute("INSERT INTO contacts(name, label, sharedkey) VALUES(?, ?, ?)",\
        (args.name, args.label, args.sharedkey)) 

    print "Name: " + args.name
    print "Label: " + args.label
    print "Shared key: " + args.sharedkey
    print "Contact was added succesfully. If you haven't already, \
    please make sure to share the label and the key values with the \
    person you want to communicate annonymously."

    return

def delete_contact(args):
    '''
    Removes a contact from the address book.
    '''

    print "Not working yet."
    return

def show_contacts(args):
    '''
    Shows all contacts in the address book.
    '''

    con = lite.connect('bar/db/bar.db')
    with con:
        cur = con.cursor() 
        cur.execute("SELECT * FROM contacts")
        rows = cur.fetchall()
        if rows:
            print "Contacts\n--------"
            for row in rows:
                print row[1]
        else:
            print "There are no contacts!"
    return

def caller(func, args):

    return func(args)

def pybar():

    operations = { 
        "contacts": {
            "add": add_contact,
            "delete": delete_contact,
            "show": show_contacts
        },
        "messages": {
            "new": send_message,
            "show": show_messages
        },
        "login": login,
        "logout": logout,
        "server": {
            "start": start_server,
            "stop": stop_server,
        },
    }

    parser = parse_cli()
    args = parser.parse_args()
    if type(operations[args.operation]) is dict:
        caller(operations[args.operation][getattr(args, args.operation + "_operation")], args)
    else:
        caller(operations[args.operation], args)

def run():
    pybar()

if __name__ == '__main__':
    run()
