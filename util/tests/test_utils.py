import unittest

from util.utils import *


class UtilsTests(unittest.TestCase):

    def test_extract_image_date(self):
        img1 = "/Users/ashah/GoogleDrive/Rilee4thGrade/June/IMG_1493.jpg"
        img2 = "/Users/ashah/GoogleDrive/Rilee4thGrade/June/IMG_1494.jpg"
        print(extract_image_date(img1))
        print(extract_image_date(img2))


    def test_get_center_of_rectangle(self):
        points = [[0.125, 95.375], [249.125, 95.375], [249.125, 269.375], [0.125, 269.375]]

        rectangle = get_rectangle_from_points(points)

        center = get_center_coods_of_rectangle(rectangle)
        print(center)

    def test_get_rectangle_from_points(self):
        print("Testing get_rectangle_from_points")
        points = [[0.125, 95.375], [249.125, 95.375], [249.125, 269.375], [0.125, 269.375]]

        rectangle = get_rectangle_from_points(points)

        print(rectangle)


if __name__ == '__main__':
    unittest.main()
