from data.processors.facedetection.MultiCNNFaceRecognizer import MultiCNNFaceRecognizer
from yearbook.page.Page import Page

import csv

"""
This class represents the Yearbook that is being created
Holds details about the school, additional details of email address, roster etc might be added to this class.
Also holds a reference to the face recognition model and probably the image similarity embedding that's being used.

"""


def create_yearbook_metadata(config_file_path, school_name, email):
    pages = []

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
                orig_image_loc = row[2]

                # Hard coded template and original image

                page = Page(number, event, personalized, orig_image_loc)
                page.print_image_name()
                line_count += 1
                pages.append(page)

        print(f'Processed {line_count} lines.')

    print("Pages in yearbook %s" % str(len(pages)))

    return Yearbook(pages, school_name, email)


class Yearbook:

    def __init__(self, pages, school, email):
        self.pages = pages
        self.school = school
        self.email = email
        self.multiCNNFaceRecognizer = MultiCNNFaceRecognizer()
        self.similarityModel = ""  # blank for now, but we probably end up adding the ResNet50 model here

    def get_drive_folders(self):
        return {page.drive_folder for page in self.pages if page.personalized}

    def get_drive_folders_with_event_name(self):
        return {(page.drive_folder, page.event_name) for page in self.pages if page.personalized}

