import unittest

from util.google.drive.util import upload_to_folder


class MyTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(MyTestCase, self).__init__(*args, **kwargs)

    def test_file_upload(self):
        pdf_file_path = "/Users/anshah/YearbookCreatorOut/anshah/.pdfs/Monticello_Preschool_2021_2022_pdfs/yearbook_stitched.pdf"
        upload_to_folder('1BsahliyczRpMHKYMofDWcWry7utS1IyM', pdf_file_path)


if __name__ == '__main__':
    unittest.main()
