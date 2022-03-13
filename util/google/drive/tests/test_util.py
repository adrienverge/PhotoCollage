import unittest

from util.google.drive.util import upload_pdf_file


class MyTestCase(unittest.TestCase):

    def test_file_upload(self):
        pdf_file_path = "/Users/ashah/GoogleDrive/YearbookCreatorOut/ashah/.pdfs/JnR_2019_2021_pdfs/yearbook.pdf"
        upload_pdf_file('1BsahliyczRpMHKYMofDWcWry7utS1IyM', pdf_file_path)


if __name__ == '__main__':
    unittest.main()
