from images.replacer.ImageReplacer import ImageReplacer
from PIL import Image

class BasicImageReplacer(ImageReplacer):

    def insert_image(self, source_image:Image, candidate_image:Image, bnd_box:[]) -> Image:
        width = bnd_box[2] - bnd_box[0]
        height = bnd_box[3] - bnd_box[1]

        resized_image = candidate_image.resize((width, height))

        bnd_box_tuple = (bnd_box[0], bnd_box[1])
        source_image.paste(resized_image, bnd_box_tuple)

        return source_image