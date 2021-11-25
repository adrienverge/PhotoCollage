import sqlite3
from sqlite3 import Error


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


def select_schools(conn):
    cur = conn.cursor()
    cur.execute("SELECT [School name] FROM School order by 1;")
    return cur.fetchall()


def get_all_rows(conn):
    cur = conn.cursor()
    query = "SELECT Distinct p.name, grade, class, r.name, c.album FROM roster r, schools p, spreads C " \
            "where r.school = p.[School ID] and c.album=p.[Album Id] order by 1,2,3,4"
    return cur.execute(query)


# This is the main entry method that takes the sqlite data base file and returns the final tree model
def get_tree_model(db_file: str):

    from gi.repository import Gtk

    treestore = Gtk.TreeStore(str)

    # Create a connection to the database
    conn = create_connection(db_file)

    all_rows = get_all_rows(conn)
    added_schools = {}

    for row in all_rows:
        school_name = '%s' % row[0]
        if school_name not in added_schools.keys():
            # add this school as a parent to the tree
            school_parent = treestore.append(None, [school_name])
            added_schools[school_name] = {}

        current_grade = '%s' % row[1]
        if current_grade not in added_schools[school_name].keys():
            grade_parent = treestore.append(school_parent, [current_grade])
            added_schools[school_name][current_grade] = {}

        current_class = '%s' % row[2]
        if current_class not in added_schools[school_name][current_grade].keys():
            class_parent = treestore.append(grade_parent, [current_class])
            added_schools[school_name][current_grade][current_class] = {}

        current_child = '%s' % row[3]
        if current_child not in added_schools[school_name][current_grade][current_class].keys():
            treestore.append(class_parent, [current_child])
            added_schools[school_name][current_grade][current_class][current_child] = {}




    return treestore




