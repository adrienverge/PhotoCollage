"""
This class will contain methods and interfaces that will operate on a single image
"""


class ItemProcessor:

    """This will take an input a path to an image and process it to produce a dictionary as an output
    At a later date, we will define the contents of the dictionary via some strong typing.
    For now, we'll assume the keys are known to the outside callers.
    """
    def process(self, source_image_path:str) -> {}:
        pass