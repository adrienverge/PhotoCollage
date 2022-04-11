import os

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

    def __init__(self, number: int, event: str, personalized: bool,
                 orig_image_loc: str, title: str, tags: str = None):
        self.number = number
        self.event_name = event
        self.personalized = personalized
        self.image = orig_image_loc
        self.data = {"imagePath": orig_image_loc,
                     "extension": os.path.splitext(orig_image_loc)[1],
                     "locked": False,
                     "pinned": False,
                     "edited": False
                     }
        self.history = []
        self.photo_list: [Photo] = []
        self.pinned_photos: {str} = set()
        self.deleted_photos: {str} = set()
        self.parent_pages: [Page] = []
        if tags == '':
            self.tags = event
        else:
            self.tags: str = tags + "," + event

        self.cleared: bool = False
        self.title = title

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def print_image_name(self):
        print("Name:: " + self.image)

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

            # Keep track of the filename that was explicitly deleted
            # This should not show up on any pages anymore.
            self.deleted_photos.add(photo_to_remove.filename)
            self.update_flag("edited", True)
        except KeyError:
            pass

    def get_parent_pinned_photos(self) -> [str]:
        _flat_list = [filename for parent_page in self.parent_pages for filename in
                      parent_page.get_all_pinned_photos()]

        return get_unique_list_insertion_order(_flat_list)

    def get_parent_deleted_photos(self) -> [str]:
        _flat_list = [filename for parent_page in self.parent_pages for filename in
                      parent_page.get_all_deleted_photos()]

        return get_unique_list_insertion_order(_flat_list)

    '''
    This method will return all pinned photos and keep track of 
    '''

    def get_all_pinned_photos(self) -> [str]:
        parent_pinned_pictures = self.get_parent_pinned_photos()
        # Keep the pictures that come from the parent at the top and append pictures from this page
        parent_pinned_pictures.extend(self.pinned_photos)
        return parent_pinned_pictures

    def get_all_deleted_photos(self) -> [str]:
        parent_deleted_pictures = self.get_parent_deleted_photos()
        # Keep the pictures that come from the parent at the top and append pictures from this page
        parent_deleted_pictures.extend(self.deleted_photos)
        return parent_deleted_pictures

    def get_filenames_parent_pins_not_on_page(self) -> [str]:
        parent_pins = self.get_parent_pinned_photos()
        photos_on_page = [photo.filename for photo in self.photo_list]
        return [filename for filename in parent_pins if filename not in photos_on_page]

    def get_parent_pins_not_on_page(self) -> [bool]:
        parent_pins = self.get_parent_pinned_photos()
        if len(parent_pins) == 0:
            return [False]

        photos_on_page = [photo.filename for photo in self.photo_list]
        return [filename not in photos_on_page for filename in parent_pins]

    def has_parent_pins_changed(self):
        import functools
        # if any of the parent_pins are missing from this page
        # then we return True
        return functools.reduce(lambda a, b: a or b, self.get_parent_pins_not_on_page(), False)

    def did_parent_delete(self):
        parent_deleted_photos = self.get_all_deleted_photos()
        # check if any existing photo is part of the parent deleted set,
        for photo in self.photo_list:
            if photo.filename in parent_deleted_photos:
                return True

        return False

    def update_flag(self, flag_name: str, flag: bool):
        self.data[flag_name] = flag

    def is_pinned(self):
        return "pinned" in self.data and self.data["pinned"]

    def is_locked(self):
        return "locked" in self.data and self.data["locked"]

    def is_edited(self):
        return "edited" in self.data and self.data["edited"]

    def clear_all(self):
        self.history = []
        self.photo_list: [Photo] = []
        self.pinned_photos: {str} = set()
        self.deleted_photos: {str} = set()
        self.data["locked"] = False
        self.data["pinned"] = False
        self.data["edited"] = False
        self.cleared = True

    @property
    def history_index(self):
        return len(self.history) - 1

    @property
    def photos_on_page(self):
        return [photo.filename for photo in self.photo_list]

    # def get_pinned_parent(self):
    #     pinned_parent = None
    #     for parent_page in self.parent_pages:
    #         if parent_page.is_pinned():
    #             pinned_parent = parent_page
    #
    #     return pinned_parent
    #
    # def get_pinned_parent_collage(self):
    #     pinned_parent = self.get_pinned_parent()
    #     if pinned_parent is not None:
    #         return pinned_parent.history[-1]
    #
    #     return None

