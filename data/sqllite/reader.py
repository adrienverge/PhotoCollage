import sqlite3
from sqlite3 import Error, Cursor, Connection
from typing import Optional


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


def get_schools(conn):
    cur = conn.cursor()
    return cur.execute("SELECT [name] FROM schools order by 1;")


def get_all_rows(db_file: str):
    conn = create_connection(db_file)
    return get_all_rows(conn)


def get_all_rows(conn):
    cur = conn.cursor()
    query = "SELECT Distinct s.name, class, r.name, p.album, p.tags FROM roster r, schools s, pages p " \
            "where r.school = s.[School ID] and p.album=s.[Album Id] order by 1,2,3,4"
    return cur.execute(query)


def get_child_orders(db_file: str, child_name: str):
    conn = create_connection(db_file)
    orders = get_order_details_for_child(conn, child_name, None)
    conn.close()

    return orders

    
def get_order_details_for_child(conn, child_name: str, school_id: str = None):
    cur = conn.cursor()
    query = 'SELECT o.product, o.[Order no.], r.id as id FROM WIXOrders o, roster r where r.name = \'%s\' and o.[' \
            'Student Id] = id' % child_name

    cursor = cur.execute(query)
    try:
        orders = []
        # Note: We have only 1 entry in the database for this child, or none 
        for row in cursor:
            orders.append((str(row[0]), str(row[1])))
    except:
        orders = None

    return orders


def get_album_details_for_school(db_file: str, school_name: str):
    conn = create_connection(db_file)
    cur = conn.cursor()
    query = 'Select a.title, a.name, a.type, a.page_number, a.image, a.tags from pages a, schools s ' \
            'where a.album = s.[Album Id] and s.name = "%s" ' % school_name

    return cur.execute(query)


def get_school_list(db_file: str):
    school_list = []
    # Create a connection to the database
    conn = create_connection(db_file)

    all_schools = get_schools(conn)
    for school in all_schools:
        # Allow JNR and Monticello as two datasets for the time being.
        if 'JnR' in school[0] or 'Mont' in school[0]:
            school_list.append(school[0])

    conn.close()

    # Provide a hard coded list for now
    school_list = ['Monticello_Preschool_2021_2022', 'JnR_2019_2021']
    return school_list
