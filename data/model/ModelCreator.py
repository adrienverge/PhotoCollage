import gi

import gi

from data.sqllite.reader import create_connection, get_schools, get_all_rows, get_order_details_for_child
from publish.OrderDetails import OrderDetails

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from yearbook.Yearbook import Yearbook, create_yearbook


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

    count_children = 0
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
            for class_page, school_page in zip(class_yearbook.pages, school_yearbook.pages):
                class_page.parent_pages.append(school_page)

            class_parent = treestore.append(school_parent, [class_yearbook])
            added_schools[school_name][current_class] = {}

        current_child = ('%s' % row[2]).strip()
        if current_child not in added_schools[school_name][current_class].keys():
            child_yearbook = create_yearbook(dir_params, school_name, classroom=current_class,
                                             child=current_child,
                                             parent_book=class_yearbook.pickle_yearbook)
            if child_yearbook is not None:
                treestore.append(class_parent, [child_yearbook])
                added_schools[school_name][current_class][current_child] = {}

                # Set the parent pages for this yearbook
                for child_page, class_page in zip(child_yearbook.pages, class_yearbook.pages):
                    child_page.parent_pages.append(class_page)

                count_children = count_children + 1
                if count_children % 10 == 0:
                    print("Added %s children" % count_children)

    print("Total number of children added %s" % count_children)
    conn.close()
    return treestore
