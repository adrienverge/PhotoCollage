import unittest

from PIL import Image

from util.utils import get_rectangle_from_points, get_center_coods_of_rectangle
from images.resizer.PILImageProcessor import get_crop_type


class PILImageProcessorTest(unittest.TestCase):

    def test_get_crop_type(self):
        img = Image.open("./IMG_0336.jpg")
        points = [[938.17993, 651.6867], [938.17993, 777.44586], [1033.7305, 651.6867], [1033.7305, 777.44586]]

        rect = get_rectangle_from_points(points)
        print(rect)

        center_x, center_y = get_center_coods_of_rectangle(rect)

        print(center_x, center_y)

        print(get_crop_type(img, [center_x, center_y]))


if __name__ == '__main__':
    unittest.main()
