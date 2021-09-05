import numpy as np
from tensorflow.keras.applications import resnet50
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing import image

_IMAGE_NET_TARGET_SIZE = (224, 224)


class Resnet50Embedding(object):

    def __init__(self):
        model = resnet50.ResNet50(weights='imagenet')
        layer_name = 'avg_pool'
        self.intermediate_layer_model = Model(inputs=model.input,
                                              outputs=model.get_layer(layer_name).output)

    def get_img_vec(self, img, ext):
        """ Gets a vector embedding from an image.
        :param ext: The file extension
        :param img: a PIL image in memory
        :returns: numpy nd-array
        """

        img = img.resize(_IMAGE_NET_TARGET_SIZE)
        if ext == ".png" or ext == "png":
            # If it's a PNG then we have to adjust the dimensions for the vector,
            # so far, the other extensions seem to be okay
            x = image.img_to_array(img)[:, :, :3]
        else:
            x = image.img_to_array(img)

        x = np.expand_dims(x, axis=0)
        x = resnet50.preprocess_input(x)
        intermediate_output = self.intermediate_layer_model.predict(x)

        return intermediate_output[0]


if __name__ == "main":
    pass
