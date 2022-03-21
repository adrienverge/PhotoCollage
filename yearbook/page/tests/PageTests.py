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

    def test_page_tags(self):
        print("Check page tags")

        page = Page.Page(number=1, event="Graduation",
                         personalized=True, orig_image_loc="./Photos10_v3.png", title="Test", tags="test")

        assert page.data is not None
        assert page.tags == "test,Graduation"


if __name__ == '__main__':
    unittest.main()
