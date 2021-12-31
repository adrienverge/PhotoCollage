from data.pickle.utils import get_pickle_path
from yearbook.page.Page import Page
from gi.repository import GObject

import csv
import pickle

"""
This class represents the Yearbook that is being created
Holds details about the school, additional details of email address, roster etc might be added to this class.
Also holds a reference to the face recognition model and probably the image similarity embedding that's being used.

"""


def create_yearbook(dir_params: {}, school_name: str, grade: str, classroom: str, child: str):
    import os

    # first lets check for pickle file
    pickle_filename = os.path.join(get_pickle_path(dir_params["output_dir"], school_name,
                                                   grade, classroom, child),
                                   "file.pickle")
    if os.path.exists(pickle_filename):
        print("Returning yearbook from pickle %s " % pickle_filename)
        return create_yearbook_from_pickle(pickle_filename)
    else:
        # Create the yearbook from DB
        return create_yearbook_from_db(dir_params, school_name, grade, classroom, child)


def create_yearbook_from_pickle(pickle_file_path):
    pickle_file = open(pickle_file_path, 'rb')
    yearbook = pickle.load(pickle_file)
    pickle_file.close()
    return yearbook


def create_yearbook_from_db(dir_params: {}, school_name: str, grade: str, classroom: str, child: str):
    import os
    pages: [Page] = []
    from data.sqllite.reader import get_album_details_for_school
    db_file_path = dir_params['db_file_path']
    corpus_base_dir = dir_params['corpus_base_dir']
    album_details = get_album_details_for_school(db_file_path, school_name)
    for row in album_details:
        personalized = False
        if row[2].startswith('Dynamic'):
            personalized = True

        page = Page(int(row[3]), str(row[1]).strip(), personalized,
                    os.path.join(corpus_base_dir, school_name, row[4]))
        print(row)
        pages.append(page)

    print("Pages in yearbook %s" % str(len(pages)))

    return Yearbook(pages, school_name, grade, classroom, child)


class Yearbook(GObject.GObject):
    school = GObject.property(type=str)
    grade = GObject.property(type=str)
    classroom = GObject.property(type=str)
    child = GObject.property(type=str)

    def __init__(self, pages: [Page], school: str):
        self.__init__(pages, school, None, None, None, None)

    def __init__(self, pages: [Page], school: str, grade: str, classroom: str, child: str):
        GObject.GObject.__init__(self)
        self.pages = pages
        self.school = school
        self.grade = grade
        self.classroom = classroom
        self.child = child
        self.parent = None

    def __repr__(self):
        if self.child is None:
            if self.classroom is None:
                if self.grade is None:
                    return self.school
                else:
                    return self.grade
            else:
                return self.classroom
        else:
            return self.child

    def store_pickled_yearbook(self, filename: str):
        from pathlib import Path
        import pickle
        import os

        path1 = Path(filename)
        # Create the parent directories if they don't exist
        os.makedirs(path1.parent, exist_ok=True)

        # Important to open the file in binary mode
        with open(filename, 'wb') as f:
            pickle.dump(self, f)

    def print_yearbook_parents(self):
        print("%s :-> %s :-> %s :-> %s" % (self.school, self.grade, self.classroom, self.child))