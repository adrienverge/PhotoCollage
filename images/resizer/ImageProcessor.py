from PIL import Image

"""
This class will contain methods and interfaces that will operate on a single image
"""
class ImageProcessor:
    """This will do a resize on the source_image and return an image of size as specified
    by the dimensions, with no additional processing"""
    def resize_image(self, source_image_path:str, dimensions:[]) -> Image:
        pass

    def crop_and_resize_image_path(self, source_image_path:str, dimensions:[], targetBox:[]) -> Image:
        pass

    def crop_and_resize_image(self, img:Image, dimensions:[], targetBox:[]) -> Image:
        pass
