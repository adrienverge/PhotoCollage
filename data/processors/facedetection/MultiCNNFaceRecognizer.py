import joblib

from PIL import Image

from data.processors.ItemProcessor import ItemProcessor

from .constants import MODEL_PATH
from data.processors.facedetection.util import draw_bb_on_img
from data.face_recognition import preprocessing


class MultiCNNFaceRecognizer(ItemProcessor):
    preprocess = preprocessing.ExifOrientationNormalize()

    def __recognise_faces__(self, img):
        return joblib.load(MODEL_PATH)(img)

    def __recognise_faces_with_box__(self, img):
        faces = MultiCNNFaceRecognizer.__recognise_faces__(img)
        if faces:
            draw_bb_on_img(faces, img)
        return faces, img

    def process(self, source_image_path: str) -> {}:
        img = Image.open(source_image_path)
        img = self.preprocess(img)
        img = img.convert('RGB')
        # Returns the faces that are found in this image
        return self.__recognise_faces__(img)
