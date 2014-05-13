import sqlite3 as lite

def update_entry(where_field, where_value, set_field, set_value):
    con = lite.connect('bar/db/bar.db')
    with con:
        cur = con.cursor()
        query = "UPDATE contacts SET %s='%s' WHERE %s='%s'" \
                % (set_field, set_value, where_field, where_value)
        cur.execute(query)
    if con:
        con.close() 

def select_entry(where_field, where_value):
    con = lite.connect('bar/db/bar.db')
    with con:
        cur = con.cursor()
        query = "SELECT * FROM contacts WHERE %s='%s'" \
                % (where_field, where_value)
        cur.execute(query)
        row = cur.fetchone()
    if con:
        con.close()
    return row
