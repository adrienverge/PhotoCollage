import unittest
from PIL import Image

from images.embeddings.Resnet50Embedding import Resnet50Embedding


class Resnet50EmbeddingsTest(unittest.TestCase):

    def test_constructor(self):
        resnet50 = Resnet50Embedding()

        assert resnet50.intermediate_layer_model is not None

    def test_img_to_vec_png(self):
        test_img = Image.open("./Photo.png")
        resnet50 = Resnet50Embedding()
        img_vect = resnet50.get_img_vec(test_img, ".png")
        assert img_vect.shape[0] == 2048

    def test_img_to_vec_jpg(self):
        test_img = Image.open("./IMG_0336.jpg")
        resnet50 = Resnet50Embedding()
        img_vect = resnet50.get_img_vec(test_img, ".jpg")
        assert img_vect.shape[0] == 2048