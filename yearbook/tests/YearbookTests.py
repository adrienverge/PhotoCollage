import unittest
import os, getpass

from data.readers.default import corpus_processor
from yearbook.Yearbook import create_yearbook, Yearbook, get_tag_list_for_page


class YearbookTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(YearbookTests, self).__init__(*args, **kwargs)
        school_name = 'Monticello_Preschool_2021_2022'
        self.corpus = corpus_processor(school_name=school_name)
        self.output_base_dir = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', 'YearbookCreatorOut')
        self.input_base_dir = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', 'YearbookCreatorInput')
        self.yearbook_parameters = {'max_count': 12,
                                    'db_file_path': os.path.join(self.input_base_dir, 'RY.db'),
                                    'output_dir': os.path.join(self.output_base_dir, getpass.getuser()),
                                    'corpus_base_dir': os.path.join('/Users', getpass.getuser(), 'GoogleDrive',
                                                                    school_name)}

    def test_yearbook_parent(self):
        school_name = 'Monticello_Preschool_2021_2022'

        school_yearbook: Yearbook = create_yearbook(self.yearbook_parameters, school_name=school_name,
                                                    classroom=None, child=None)

        class_yearbook: Yearbook = create_yearbook(self.yearbook_parameters, school_name=school_name,
                                                   classroom="AdventureLand", child=None,
                                                   parent_book=school_yearbook.pickle_yearbook)

        assert class_yearbook.pickle_yearbook.parent_book.__repr__() == school_yearbook.__repr__()

    def test_get_tags_for_page(self):
        school_name = "JnR_2019_2021"
        school_yearbook: Yearbook = create_yearbook(self.yearbook_parameters, school_name=school_name,
                                                    classroom=None, child=None)

        tag_list = get_tag_list_for_page(school_yearbook, school_yearbook.pages[22])
        assert school_yearbook.pages[22].event_name in tag_list
        assert school_name in tag_list

    def test_get_tags_for_page_school(self):
        school_name = "Monticello_Preschool_2021_2022"
        school_yearbook: Yearbook = create_yearbook(self.yearbook_parameters, school_name=school_name,
                                                    classroom=None, child=None)

        tag_list = get_tag_list_for_page(school_yearbook, school_yearbook.pages[22])
        assert school_yearbook.pages[22].event_name in tag_list
        assert school_name in tag_list

    def test_get_tags_for_page_classroom(self):
        school_name = "Monticello_Preschool_2021_2022"
        classroom_name = 'AdventureLand'
        school_yearbook: Yearbook = create_yearbook(self.yearbook_parameters, school_name=school_name,
                                                    classroom=classroom_name, child=None)

        tag_list = get_tag_list_for_page(school_yearbook, school_yearbook.pages[22])
        assert school_yearbook.pages[22].event_name in tag_list
        assert school_name in tag_list
        assert classroom_name in tag_list

    if __name__ == '__main__':
        unittest.main()
