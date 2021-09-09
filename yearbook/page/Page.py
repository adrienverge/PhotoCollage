import os

"""
    A representation of a Page in the context of Rethink yearbooks
    TODO:: Need to store the final created canvas with the page.
    This should simplify the creation of the final PDF.
"""


def read_page_json(json_file_loc):
    import json
    print('Reading json from ', json_file_loc)
    with open(json_file_loc) as json_file:
        data = json.load(json_file)

    return data


class Page:

    def __init__(self, number: int, event: str, personalized: bool, orig_image_loc: str):
        self.number = number
        self.event_name = event
        self.personalized = personalized
        self.image = orig_image_loc
        self.data = {"imagePath": orig_image_loc, "extension": os.path.splitext(orig_image_loc)[1]}
        self.history = []
        self.history_index = 0
        self.final_image = None

    def print_image_name(self):
        print("Name:: " + self.image)
