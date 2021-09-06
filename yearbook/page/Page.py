from util.utils import get_rectangle_from_points
from images.embeddings.Resnet50Embedding import Resnet50Embedding

import os
from PIL import Image


def get_cropped_image_with_label(page_img, points, label):
    """
    This method will crop a part of the image and return a label and the actual cropped image object
    :param points: The x, y locations of the section that needs to be cropped
    :param label: The label that identifies this section/image
    :param page_img: the full image where a section needs to be cropped from
    :return: A tuple containing the label and its associated cropped image
    """
    return label, page_img.crop((points[0], points[1], points[2], points[3]))


"""
    Read the templated marked up json file
"""


def read_page_json(json_file_loc):
    import json
    print('Reading json from ', json_file_loc)
    with open(json_file_loc) as json_file:
        data = json.load(json_file)

    return data


class Page:

    def __init__(self, number: int, event: str, personalized: bool, drive_folder: str, template_loc: str,
                 orig_image_loc: str):
        self.number = number
        self.event_name = event
        self.personalized = personalized
        self.template_location = template_loc
        self.drive_folder = drive_folder
        self.data = read_page_json(template_loc)
        self.image = orig_image_loc
        self.data["imagePath"] = orig_image_loc
        self.data["extension"] = os.path.splitext(orig_image_loc)[1]
        self.history = []
        self.history_index = 0
        #self.model = Resnet50Embedding()
        #self.generate_cropped_image_vectors()

    def print_image_name(self):
        print("Name:: " + self.image)

    def generate_cropped_image_vectors(self):
        full_page_image = Image.open(self.data["imagePath"])

        # create a rectangle from the data that is presented in shapes
        # for each of the bounding boxes, we should retrieve the cropped image
        cropper = map(lambda x: get_cropped_image_with_label(full_page_image, get_rectangle_from_points(x['points']),
                                                             label=x['label']), self.data['shapes'])
        cropped_images = list(cropper)

        # The tolist() is added here, so that we can write the vectors to a json file;
        image_vectors = list(
            map(lambda x: (x[0], self.model.get_img_vec(x[1], self.data["extension"]).tolist()), cropped_images))

        self.data["image_vect_dict"] = dict((x, y) for x, y in image_vectors)