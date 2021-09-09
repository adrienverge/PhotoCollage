import unittest

from yearbook.page import Page


def check_key(dict_map, key):
    if key in dict_map.keys():
        print("Present, ", end=" ")
        return True
    else:
        print("Not present")
        return False


class PageTests(unittest.TestCase):

    def test_generate_cropped_image_vectors(self):
        print("Running Test for checking img vectors")

        page = Page.Page(number=1, event="Graduation", personalized=True, orig_image_loc="./Photos10_v3.png")

        assert page.data is not None


if __name__ == '__main__':
    unittest.main()
