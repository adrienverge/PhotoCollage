"""
A template creator class that's responsible for creating a template that will be used to place images
"""
from page import Page


class Creator:

    """
    The purpose of this interface is to return a Page.
    For the time being, this Creator just reads the json from a path and returns
    the Page object that holds the bounding boxes.

    In future, we imagine this template creator to have different creation capabilities,

    This instance of this creator, can be a FileReadingCreator which reads the json from a file to return a Page.

    Additionally we can have a random template creator that picks randomly from a series of templates to pick one

    """
    def process(self, source_image_path:str) -> Page :
        import json
        print('Reading page json from ', source_image_path)
        with open(source_image_path) as json_file:
            data = json.load(json_file)

        return Page(image=data['imagePath'], data_map=data)