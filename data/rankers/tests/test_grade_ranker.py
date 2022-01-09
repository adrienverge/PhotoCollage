import unittest
import os, getpass

from data.rankers import RankerFactory
from data.readers.default import corpus_processor
from yearbook.Yearbook import create_yearbook
from yearbook.page import Page


class TestGradeRanker(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(TestGradeRanker, self).__init__(*args, **kwargs)
        self.corpus = corpus_processor(school_name='Monticello_Preschool_2021_2022')
        self.output_base_dir = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', 'YearbookCreatorOut')
        self.yearbook_parameters = {'max_count': 12,
                                    'db_file_path': os.path.join(self.output_base_dir, 'RY.db'),
                                    'output_dir': os.path.join(self.output_base_dir, getpass.getuser()),
                                    'corpus_base_dir': os.path.join('/Users', getpass.getuser(), 'GoogleDrive',
                                                                    'Monticello_Preschool_2021_2022')}
        self.yearbook = create_yearbook(self.yearbook_parameters, school_name='Monticello_Preschool_2021_2022',
                                        grade='PreK', classroom=None, child=None)

    def get_images_for_page(self, page: Page, max_count: int = 20):
        ranker = RankerFactory.create_ranker(self.corpus, self.yearbook)
        images = ranker.get_candidate_images(self.yearbook, page, max_count)
        print(ranker.who_am_i())
        return images

    def test_1(self):
        tag_list = []

        # Original page tags are a string, we need to split to make it a list
        tag_list.extend(["Sunshine"])
        tag_list.append("Portraits")
        tag_list.append("Monticello_Preschool_2021_2022")
        tag_list.append("PreK")

        # Return a list of images that are applicable to the grade
        images = self.corpus.get_intersection_images(tag_list)
        [print(img) for img in images]


    def test_ranker_page_5(self):
        page5 = self.yearbook.pages[4]
        images = self.get_images_for_page(page5, 100)
        assert 1 == len(page5.tags.split(","))
        assert 0 <= images.index('/Users/ashah/GoogleDrive/Monticello_Preschool_2021_2022/Sunshine/Portraits/Sophie Wu_1.png')
        assert page5.number == 5
        assert page5.event_name == "Portraits"
        assert len(images) == 100

    def test_portraits_jungle(self):
        page6 = self.yearbook.pages[5]
        images = self.get_images_for_page(page6)
        print(page6.tags)
        [print(img) for img in images]
        assert len(images) == 20

    def test_ranker_first_day_of_school_1(self):
        first_day_of_school_1 = self.yearbook.pages[13]
        images = self.get_images_for_page(first_day_of_school_1, 500)
        print("Number of %s images %s" % (first_day_of_school_1.event_name, str(len(images))))

        assert 1 == len(first_day_of_school_1.tags.split(","))

        assert first_day_of_school_1.number == 14
        assert first_day_of_school_1.event_name == "FirstDayOfSchool"

    def test_ranker_first_day_of_school_2(self):
        first_day_of_school_2 = self.yearbook.pages[14]
        images = self.get_images_for_page(first_day_of_school_2, 500)
        print("Number of %s images %s" % (first_day_of_school_2.event_name, str(len(images))))

        assert 1 == len(first_day_of_school_2.tags.split(","))

        assert first_day_of_school_2.number == 15
        assert first_day_of_school_2.event_name == "FirstDayOfSchool"

    def test_ranker_page_15(self):
        page15 = self.yearbook.pages[15]
        images = self.get_images_for_page(page15, 500)
        assert 1 == len(page15.tags.split(","))

        assert page15.number == 16
        assert page15.event_name == "Walkathon"
        print("Number of walkathon images %s" % str(len(images)))

    if __name__ == '__main__':
        unittest.main()
