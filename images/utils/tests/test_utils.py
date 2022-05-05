import unittest

from images.utils import get_date_taken


class TestUtils(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(TestUtils, self).__init__(*args, **kwargs)

    def test_date_taken(self):
        from PIL import Image
        photo1 = "/Users/anshah/GoogleDrive/Vargas_2021_2022/SpiritDays/20220304_081157.jpg"
        print(Image.open(photo1)._getexif())