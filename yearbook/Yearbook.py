from data.pickle.utils import get_pickle_path
from yearbook.page.Page import Page
from gi.repository import GObject

import pickle

"""
This class represents the Yearbook that is being created
Holds details about the school, additional details of email address, roster etc might be added to this class.
Also holds a reference to the face recognition model and probably the image similarity embedding that's being used.

"""


def create_yearbook(dir_params: {}, school_name: str, classroom: str, child: str, parent_book=None):
    import os

    # first lets check for pickle file
    pickle_filename = os.path.join(get_pickle_path(dir_params["output_dir"], school_name,
                                                   classroom, child),
                                   "file.pickle")
    if os.path.exists(pickle_filename):
        print("Returning yearbook from pickle %s " % pickle_filename)
        return create_yearbook_from_pickle(pickle_filename)
    else:
        # Create the yearbook from DB
        return create_yearbook_from_db(dir_params, school_name, classroom, child, parent_book)


def create_yearbook_from_pickle(pickle_file_path):
    pickle_file = open(pickle_file_path, 'rb')
    yearbook: PickleYearbook = pickle.load(pickle_file)
    pickle_file.close()
    return Yearbook(pickle_yearbook=yearbook)


def create_yearbook_from_db(dir_params: {}, school_name: str, classroom: str, child: str, parent_book=None):
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
                    os.path.join(corpus_base_dir, school_name, row[4]), str(row[5]))
        pages.append(page)

    return Yearbook(PickleYearbook(pages, school_name, classroom, child, parent_book))


class PickleYearbook:

    def __init__(self, pages: [Page], school: str, classroom: str, child: str, parent_book):
        self.pages = pages
        self.school: str = school
        self.classroom: str = classroom
        self.child: str = child
        self.parent_book: PickleYearbook = parent_book

    def __repr__(self):
        if self.child is None:
            if self.classroom is None:
                return self.school
            else:
                return self.classroom
        else:
            return self.child

    def print_yearbook_info(self):
        print("%s :-> %s :-> %s" % (self.school,
                                    self.classroom, self.child))


class Yearbook(GObject.GObject):

    def __init__(self, pickle_yearbook: PickleYearbook):
        GObject.GObject.__init__(self)
        self.pickle_yearbook = pickle_yearbook
        self.pages = self.pickle_yearbook.pages
        self.school = self.pickle_yearbook.school
        self.classroom = self.pickle_yearbook.classroom
        self.child = self.pickle_yearbook.child
        self.parent_yearbook = self.pickle_yearbook.parent_book

    def get_prev_page(self, current_page: Page):
        current_page_idx = current_page.number - 1
        if current_page_idx == 0:
            prev_page_idx = 0
        else:
            prev_page_idx = current_page_idx - 1

        return self.pages[prev_page_idx]

    def __repr__(self):
        if self.pickle_yearbook.child is None:
            if self.pickle_yearbook.classroom is None:
                return self.pickle_yearbook.school
            else:
                return self.pickle_yearbook.classroom

        return self.pickle_yearbook.child

    def print_yearbook_info(self):
        print("%s :-> %s :-> %s" % (self.pickle_yearbook.school,
                                    self.pickle_yearbook.classroom, self.pickle_yearbook.child))


def get_tag_list_for_page(yearbook: Yearbook, page: Page):
    tags = []
    if yearbook.school is not None:
        tags.append(yearbook.school)

    if yearbook.classroom is not None:
        tags.append(yearbook.classroom)

    if yearbook.child is not None:
        tags.append(yearbook.child)

    if page.tags is not None or page.tags != 'None':
        tags.extend(page.tags.split(","))

    tags.append(page.event_name)

    try:
        tags.remove('None')
    except ValueError:
        pass

    return tags
