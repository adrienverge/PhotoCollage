import os
import PIL.Image

from photocollage.collage import Photo
from util.utils import get_unique_list_insertion_order

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
        self.final_image: PIL.Image = None
        self.photo_list: [Photo] = []
        self.pinned_photos: {str} = set()
        self.parent_pages: [Page] = []

    def print_image_name(self):
        print("Name:: " + self.image)

    def update_final_image(self, canvas: PIL.Image):
        self.final_image = canvas

    def pin_photo(self, photo: Photo):
        # find the photo in the list of photos, it's always going to be in there
        photo_to_pin: Photo = next(x for x in self.photo_list if x.filename == photo.filename)
        self.pinned_photos.add(photo_to_pin.filename)

    def remove_pinned_photo(self, photo: Photo):
        try:
            photo_to_unpin: Photo = next(x for x in self.photo_list if x.filename == photo.filename)
            self.pinned_photos.remove(photo_to_unpin.filename)
        except KeyError:
            pass

    def remove_from_photolist(self, photo: Photo):
        try:
            photo_to_remove: Photo = next(x for x in self.photo_list if x.filename == photo.filename)
            self.photo_list.remove(photo_to_remove)
        except KeyError:
            pass

    def get_parent_pinned_photos(self) -> [str]:
        _flat_list = [filename for parent_page in self.parent_pages for filename in
                      parent_page.get_all_pinned_photos()]

        return get_unique_list_insertion_order(_flat_list)

    '''
    This method will return all pinned photos and keep track of 
    '''

    def get_all_pinned_photos(self) -> [str]:
        parent_pinned_pictures = self.get_parent_pinned_photos()
        # Keep the pictures that come from the parent at the top and append pictures from this page
        parent_pinned_pictures.extend(self.pinned_photos)
        return parent_pinned_pictures
