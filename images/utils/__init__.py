from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input
import numpy as np


def generate_vector_from_img(image_file, model):
    """
    Given an image this generated a feature vector for that image
    :param image_file: An image, for which a feature vector can be generated
    :return: A feature vector associated with that image.
    """

    print("creating vector for image", image_file)
    img = image.load_img(image_file, target_size=(224, 224))

    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)

    x = preprocess_input(x)

    return image_file, model.predict(x)


def get_orientation_fixed_pixbuf(img: str):
    import PIL, gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GdkPixbuf', '2.0')

    from gi.repository import GdkPixbuf

    try:
        pil_image = PIL.Image.open(img)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=img,
            width=120,
            height=120,
            preserve_aspect_ratio=True)

        exif = pil_image._getexif()
        if exif is not None and 274 in exif:  # orientation tag
            orientation = exif[274]
            if orientation == 3:
                pixbuf=pixbuf.rotate_simple(180)
            elif orientation == 6:
                pixbuf=pixbuf.rotate_simple(270)
            elif orientation == 8:
                pixbuf=pixbuf.rotate_simple(90)
    except OSError:
        # raise BadPhoto(name)
        print("Skipping a photo: %s" % img)

    return pixbuf