import sqlite3
from sqlite3 import Error
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from yearbook.Yearbook import Yearbook, create_yearbook


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


def get_all_rows(conn):
    cur = conn.cursor()
    query = "SELECT Distinct s.name, class, r.name, p.album, p.tags FROM roster r, schools s, pages p " \
            "where r.school = s.[School ID] and p.album=s.[Album Id] order by 1,2,3,4"
    return cur.execute(query)


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


def get_school_list_model(db_file: str):
    from gi.repository import Gtk

    school_list_store = Gtk.ListStore(str)
    # Create a connection to the database
    conn = create_connection(db_file)

    all_schools = get_schools(conn)
    for school in all_schools:
        school_list_store.append(school)

    conn.close()
    return school_list_store


# This is the main entry method that takes the sqlite data base file and returns the final tree model
def get_tree_model(dir_params: {}, school_selection: str) -> Gtk.TreeStore:
    treestore = Gtk.TreeStore(Yearbook)

    db_file = dir_params['db_file_path']
    # Create a connection to the database
    conn = create_connection(db_file)

    all_rows = get_all_rows(conn)
    added_schools = {}

    for row in all_rows:
        school_name = ('%s' % row[0]).strip()
        if school_selection != school_name:
            continue

        if school_name not in added_schools.keys():
            # add this school as a parent to the tree
            # Create the school level yearbook here
            school_yearbook: Yearbook = create_yearbook(dir_params, school_name, classroom=None, child=None)
            school_parent = treestore.append(None, [school_yearbook])
            added_schools[school_name] = {}

        current_class = ('%s' % row[1]).strip()
        if current_class not in added_schools[school_name].keys():
            class_yearbook = create_yearbook(dir_params, school_name, classroom=current_class,
                                             child=None, parent_book=school_yearbook.pickle_yearbook)

            # Set the parent pages for this yearbook
            [class_page.parent_pages.append(school_page) for class_page, school_page in
             zip(class_yearbook.pages, school_yearbook.pages)]

            class_parent = treestore.append(school_parent, [class_yearbook])
            added_schools[school_name][current_class] = {}

        current_child = ('%s' % row[2]).strip()
        if current_child not in added_schools[school_name][current_class].keys():
            child_yearbook = create_yearbook(dir_params, school_name, classroom=current_class,
                                             child=current_child,
                                             parent_book=class_yearbook.pickle_yearbook)

            treestore.append(class_parent, [child_yearbook])
            added_schools[school_name][current_class][current_child] = {}

            # Set the parent pages for this yearbook
            [child_page.parent_pages.append(class_page) for child_page, class_page in
             zip(child_yearbook.pages, class_yearbook.pages)]

    conn.close()
    return treestore
