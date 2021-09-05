from images.resizer.ImageProcessor import ImageProcessor
from PIL import Image


class BasicImageProcessor(ImageProcessor):

    """
    This is a very basic resize operation and returns a new image that will be the
    original image, resized to the given input dimensions.
    This processor doesn't need any additional information to resize the image
    """
    def resize_image(self, source_image_path:str, dimensions:[]) -> Image:
        source_image = Image.open(source_image_path)
        img_size = (dimensions[0], dimensions[1])
        return source_image.resize(img_size)