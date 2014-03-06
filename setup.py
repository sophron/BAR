#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3 as lite
import sys

from setuptools import setup, find_packages

setup(
    name = "bar",
    author = "sophron",
    author_email = "sophron@latthi.com",
    description = ("A broadcast anonymity network"),
    license = "BSD",
    keywords = ['anonymity', 'broadcast', 'twisted'],

    packages = find_packages(),
    entry_points = {
        'console_scripts': [
            'bar = bar.pybar:run'
            ]
        },

    install_requires = [
        'setuptools',
        'PyCrypto',
        'Twisted',
        'argparse',
        'pyptlib >= 0.0.5'
        ],
)


con = lite.connect('bar/db/bar.db')

with con: 
    cur = con.cursor()
    cur.execute("CREATE TABLE contacts(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, label TEXT, publickey TEXT, sharedkey TEXT)")
    cur.execute("CREATE TABLE clients(id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT, port INT, timelogout TEXT)")
    cur.execute("CREATE TABLE messages(id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT)")
    cur.execute("CREATE TABLE history(id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, time TEXT)")

    cur.execute("CREATE UNIQUE INDEX 'id_UNIQUE' ON 'contacts' ('id' ASC);")
