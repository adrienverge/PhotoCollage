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
