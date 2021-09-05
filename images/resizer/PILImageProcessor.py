from images.resizer.ImageProcessor import ImageProcessor
from PIL import Image


def get_crop_type(img: Image, top_left: (float, float)) -> str:
    (_width, _height) = img.size

    if top_left is None:
        return "middle"

    try:
        if top_left[1] < _height/3.0:
            print("#### returning top ...")
            return "top"
        elif top_left[1] < _height * 2/3.0:
            return "middle"
        else:
            print("#### returning bottom ...")
            return "bottom"
    except IndexError:
        return "middle"


class PILImageProcessor(ImageProcessor):
    """
    This is a very basic resize operation and returns a new image that will be the
    original image, resized to the given input dimensions.
    This processor doesn't need any additional information to resize the image
    """

    def resize_image(self, source_image_path: str, dimensions: []) -> Image:
        return self.crop_and_resize_image(source_image_path, dimensions, [])

    def crop_and_resize_image_path(self, source_image_path: str, target_dimensions: [], face_bnd_box: []) -> Image:
        img = Image.open(source_image_path)
        self.crop_and_resize_image(img, target_dimensions, face_bnd_box)

    def crop_and_resize_image(self, img: Image, target_dimensions: [], face_bnd_box: []) -> Image:
        """
            Resize and crop an image to fit the specified size.

            args:
            img: PIL image.
            target_dimensions: `(width, height)` tuple.
            face_bnd_box: This is used to determine where should be the image be cropped, top, middle or bottom.
            This is going to be 4 points to begin with, left=2584.0571, top=953.75354, right=2603.5818, bottom=979.99786
            for e.g in a single array
            raises:
            Exception: if can not open the file in img_path of there is problems
            to save the image.
            ValueError: if an invalid `crop_type` is provided.
        """
        # If height is higher we resize vertically, if not we resize horizontally
        crop_type = get_crop_type(img, (face_bnd_box[0], face_bnd_box[1]))
        # Get current and desired ratio for the images
        img_ratio = img.size[0] / float(img.size[1])
        ratio = target_dimensions[0] / float(target_dimensions[1])
        # The image is scaled/cropped vertically or horizontally depending on the ratio
        if ratio > img_ratio:
            img = img.resize((target_dimensions[0], int(round(target_dimensions[0] * img.size[1] / img.size[0]))),
                             Image.ANTIALIAS)
            # Crop in the top, middle or bottom
            if crop_type == 'top':
                box = (0, 0, img.size[0], target_dimensions[1])
            elif crop_type == 'middle':
                box = (0, int(round((img.size[1] - target_dimensions[1]) / 2)), img.size[0],
                       int(round((img.size[1] + target_dimensions[1]) / 2)))
            elif crop_type == 'bottom':
                box = (0, img.size[1] - target_dimensions[1], img.size[0], img.size[1])
            else:
                raise ValueError('ERROR: invalid value for crop_type')
            img = img.crop(box)
        elif ratio < img_ratio:
            img = img.resize((int(round(target_dimensions[1] * img.size[0] / img.size[1])), target_dimensions[1]),
                             Image.ANTIALIAS)
            # Crop in the top, middle or bottom
            if crop_type == 'top':
                box = (0, 0, target_dimensions[0], img.size[1])
            elif crop_type == 'middle':
                box = (int(round((img.size[0] - target_dimensions[0]) / 2)), 0,
                       int(round((img.size[0] + target_dimensions[0]) / 2)), img.size[1])
            elif crop_type == 'bottom':
                box = (img.size[0] - target_dimensions[0], 0, img.size[0], img.size[1])
            else:
                raise ValueError('ERROR: invalid value for crop_type')
            img = img.crop(box)
        else:
            img = img.resize((target_dimensions[0], target_dimensions[1]),
                             Image.ANTIALIAS)

        # If the scale is the same, we do not need to crop
        print("Resized image to ", img.size)
        return img
