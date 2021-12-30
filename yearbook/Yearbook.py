from yearbook.page.Page import Page

import csv

"""
This class represents the Yearbook that is being created
Holds details about the school, additional details of email address, roster etc might be added to this class.
Also holds a reference to the face recognition model and probably the image similarity embedding that's being used.

"""


def create_yearbook_metadata_from_csv(config_file_path, school_name, email):
    pages: [Page] = []

    with open(config_file_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                number = int(row[0])
                event = row[1].strip().replace(" ", "_")  # Remove spaces and replace spaces with underscores
                if row[2].strip() == 'yes':
                    personalized = True
                else:
                    personalized = False
                orig_image_loc = row[3]

                # Hard coded template and original image

                page = Page(number, event, personalized, orig_image_loc)
                page.print_image_name()
                line_count += 1
                pages.append(page)

        print(f'Processed {line_count} lines.')

    print("Pages in yearbook %s" % str(len(pages)))

    return Yearbook(pages, school_name, email)


def create_yearbook_from_pickle(pickle_file_path):
    from data.pickle.utils import load_pickled_yearbook
    return load_pickled_yearbook(pickle_file_path)


def create_yearbook_from_db(db_file_path, school_name, email='anuj.for@gmail.com'):
    import os
    pages: [Page] = []
    from data.sqllite.reader import get_album_details_for_school
    album_details = get_album_details_for_school(db_file_path, school_name)
    for row in album_details:
        personalized = False
        if row[2].startswith('Dynamic'):
            personalized = True

        page = Page(int(row[3]), str(row[1]).strip(), personalized, os.path.join(os.path.dirname(db_file_path), school_name, row[4]))
        print(row)
        pages.append(page)

    print("Pages in yearbook %s" % str(len(pages)))

    return Yearbook(pages, school_name, email)


class Yearbook:

    def __init__(self, pages: [Page], school: str, email: str):
        self.pages = pages
        self.school = school
        self.email = email

    def get_drive_folders(self):
        return {page.drive_folder for page in self.pages if page.personalized}

    def get_drive_folders_with_event_name(self):
        return {(page.drive_folder, page.event_name) for page in self.pages if page.personalized}
