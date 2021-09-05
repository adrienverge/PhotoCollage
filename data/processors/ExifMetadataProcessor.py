from corpus.processors.ItemProcessor import ItemProcessor

from PIL import Image
from PIL.ExifTags import TAGS


class ExifMetadataProcessor(ItemProcessor):

    def get_metadata_jpg(self, source_image_path:str) -> {}:
        image = Image.open(source_image_path)
        exifdata = image.getexif()

        # iterating over all EXIF data fields
        for tag_id in exifdata:
            # get the tag name, instead of human unreadable tag id
            tag = TAGS.get(tag_id, tag_id)
            data = exifdata.get(tag_id)
            # decode bytes
            if isinstance(data, bytes):
                data = data.decode()
            print(f"{tag:25}: {data}")

        return {}

    def get_metadata_png(self, source_image_path:str) -> {}:
        im = Image.open(source_image_path)
        im.load()  # Needed only for .png EXIF data (see citation above)
        print(im.info['meta_to_read'])
        return {}

    def process(self, source_image_path:str) -> {}:

        if source_image_path.endswith(".jpg"):
            metadata = self.get_metadata_jpg(source_image_path)
        else:
            metadata = self.get_metadata_png(source_image_path)

        return metadata
