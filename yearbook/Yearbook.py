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
    yearbook: PickleYearbook = pickle.load(pickle_file)
    pickle_file.close()
    return Yearbook(pickle_yearbook=yearbook)


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

    return Yearbook(PickleYearbook(pages, school_name, grade, classroom, child))


def store_pickled_yearbook(yearbook, filename: str):
    from pathlib import Path
    import pickle
    import os

    path1 = Path(filename)
    # Create the parent directories if they don't exist
    os.makedirs(path1.parent, exist_ok=True)

    # Important to open the file in binary mode
    with open(filename, 'wb') as f:
        pickle.dump(yearbook.pickle_yearbook, f)


class PickleYearbook:
    def __init__(self, pages: [Page], school: str):
        self.__init__(pages, school, None, None, None, None)

    def __init__(self, pages: [Page], school: str, grade: str, classroom: str, child: str):
        self.pages = pages
        self.school: str = school
        self.grade: str = grade
        self.classroom: str = classroom
        self.child: str = child


class Yearbook(GObject.GObject):

    def __init__(self, pickle_yearbook: PickleYearbook):
        GObject.GObject.__init__(self)
        self.pickle_yearbook = pickle_yearbook
        self.pages = self.pickle_yearbook.pages
        self.school = self.pickle_yearbook.school
        self.grade = self.pickle_yearbook.grade
        self.classroom= self.pickle_yearbook.classroom
        self.child = self.pickle_yearbook.child

    def __repr__(self):
        if self.pickle_yearbook.child is None:
            if self.pickle_yearbook.classroom is None:
                if self.pickle_yearbook.grade is None:
                    return self.pickle_yearbook.school
                else:
                    return self.pickle_yearbook.grade
            else:
                return self.pickle_yearbook.classroom
        else:
            return self.pickle_yearbook.child

    def print_yearbook_parents(self):
        print("%s :-> %s :-> %s :-> %s" % (self.pickle_yearbook.school, self.pickle_yearbook.grade,
                                           self.pickle_yearbook.classroom, self.pickle_yearbook.child))
