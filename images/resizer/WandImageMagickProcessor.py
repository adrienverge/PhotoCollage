from images.resizer.ImageProcessor import ImageProcessor
from wand.image import Image


class WandImageMagickProcessor(ImageProcessor):

    """
    This is a very basic resize operation and returns a new image that will be the
    original image, resized to the given input dimensions.
    This processor doesn't need any additional information to resize the image
    """
    def resize_image(self, source_image_path:str, dimensions:[]) -> Image:
        width = dimensions[0]
        height = dimensions[1]
        source_image = Image(filename=source_image_path)
        portrait = source_image.width < source_image.height
        if portrait:
            image_size = source_image.size
            keywords = 'top', 'left', 'height', 'width'
        else:
            image_size = source_image.height, source_image.width
            keywords = 'left', 'top', 'width', 'height'

        crop_size = int(image_size[0] * height / width)
        args = (int((image_size[1] - crop_size) / 2), 0, crop_size, image_size[0])
        source_image.crop(**dict(zip(keywords, args)))
        source_image.resize(width, height, 'lanczos')

        return source_image
