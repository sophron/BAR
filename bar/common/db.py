#!/usr/bin/env python

import sqlite3
import logging

# TODO: Grab this from constants file.
DBFILE = "bar/db/bar.db"

class Bardb():
    """ Interface for db storage. Serves as segregation of the persistence layer 
    and the application logic
    """ 
    def __init__(self):
        self.con = False
        #self._log = logging.getLogger('DB')

    def _connect_to_db(self):
        """ Opens a db connection
        """
        self.con = sqlite3.connect(DBFILE)
        self.con.row_factory = self._dictFactory

    def _disconnect_from_db(self):
        """ Close the db connection
        """
        if self.con:
           self.con.close()       
        self.con = False
 
    def _dictFactory(self, cursor, row):
        """ A factory that allows sqlite to return a dictionary instead of a tuple
        """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get_or_create(self, table, get_where_dict, operator="AND"):
        """ This method attempts to grab the record first. If it fails to find it, 
        it will create it.
        @param table: The table to search to
        @param get_where_dict: A dictionary with the WHERE/SET clauses
        """
        entries = self.select_entries(table, get_where_dict, operator)
        if len(entries) == 0:
            self.insert_entry(table, get_where_dict)
        return self.select_entries(table, get_where_dict, operator)[0]
        

    def update_entries(self, table, where_dict, set_dict, operator="AND"):
        """ A wrapper for the SQL UPDATE operation
        @param table: The table to search to
        @param whereDict: A dictionary with the WHERE clauses
        @param setDict: A dictionary with the SET clauses
        """

        self._connect_to_db()
        with self.con:
            cur = self.con.cursor()
            first = True
            for key, value in set_dict.iteritems():
                if first:
                    set_part = "%s = '%s'" % (key, value)
                    first = False
                else:
                    set_part = set_part + ", %s = '%s'" % (key, value)
            first = True
            for key, value in where_dict.iteritems():
                if first: 
                    where_part = "%s = '%s'" % (key, value)
                    first = False
                else:
                    where_part = where_part + "%s %s = '%s'" % (operator, key, value)
            query = "UPDATE %s SET %s WHERE %s" \
                    % (table, set_part, where_part)
            #self._log.info('query: %s' % query)
            cur.execute(query)
        self._disconnect_from_db()

    def insert_entry(self, table, update_dict):
        """ A wrapper for the SQL INSERT operation
        @param table: The table to search to
        @param updateDict: A dictionary with the values to set
        """
        self._connect_to_db()
        with self.con:
            cur = self.con.cursor()
            first = True
            for key, value in update_dict.iteritems():
                if first: 
                    updatefield_part = "%s" % (key)
                    setfield_part = "'%s'" % (value)
                    first = False
                else:
                    updatefield_part = updatefield_part + ", %s" % (key)
                    setfield_part = setfield_part + ", '%s'" % (value)
            query = "INSERT INTO %s(%s) VALUES(%s)"  \
                    % (table, updatefield_part, setfield_part)
            cur.execute(query)
            #self._log.info("query: %s "% query)
        self._disconnect_from_db()

    def select_entries(self, table, where_dict={"'1'":"1"}, operator="AND", order_field="id", order="ASC"):
        """ A wrapper for the SQL SELECT operation. It will always return all the 
            attributes for the selected rows.
        @param table: The table to search to
        @param whereDict: A dictionary with the WHERE clauses. If ommited it will 
        return all the rows of the table
        """
        self._connect_to_db()
        with self.con:
            cur = self.con.cursor()
            first = True
            for key, value in where_dict.iteritems():
                if first: 
                    where_part = "%s = '%s'" % (key, value)
                    first = False
                else:
                    where_part = where_part + "%s %s = '%s'" % (operator, key, value)
            query = "SELECT * FROM %s WHERE %s ORDER BY %s %s" \
                    % (table, where_part, order_field, order)
            #self._log.info("query: %s "% query)
            cur.execute(query)
            rows = cur.fetchall()                
        self._disconnect_from_db()
        return rows

    def delete_entries(self, table, where_dict={"'1'":"1"}):
        """ A wrapper for the SQL DELETE operation. It will always return all the 
            attributes for the selected rows.
        @param table: The table to search to
        @param whereDict: A dictionary with the WHERE clauses. If ommited it will 
        delete all the rows of the table

        """

        self._connect_to_db()
        with self.con:
            cur = self.con.cursor()
            first = True
            for key, value in where_dict.iteritems():
                if first: 
                    where_part = "%s = '%s'" % (key, value)
                    first = False
                else:
                    where_part = where_part + ", %s = '%s'" % (key, value)
            query = "DELETE FROM %s WHERE %s" \
                    % (table, where_part)
            #self._log.info('query: %s' % query)
            cur.execute(query)
        self._disconnect_from_db()
