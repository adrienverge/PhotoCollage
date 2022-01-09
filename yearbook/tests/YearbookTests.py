import unittest
import os, getpass

from data.readers.default import corpus_processor
from yearbook.Yearbook import create_yearbook, Yearbook


class YearbookTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(YearbookTests, self).__init__(*args, **kwargs)
        self.corpus = corpus_processor(school_name='Monticello_Preschool_2021_2022')
        self.output_base_dir = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', 'YearbookCreatorOut')

    def test_yearbook_parent(self):
        school_name = 'Monticello_Preschool_2021_2022'
        yearbook_parameters = {'max_count': 12,
                               'db_file_path': os.path.join(self.output_base_dir, 'RY.db'),
                               'output_dir': os.path.join(self.output_base_dir, getpass.getuser()),
                               'corpus_base_dir': os.path.join('/Users', getpass.getuser(), 'GoogleDrive',
                                                               school_name)}

        school_yearbook: Yearbook = create_yearbook(yearbook_parameters, school_name=school_name,
                                          grade=None, classroom=None, child=None)

        grade_yearbook: Yearbook = create_yearbook(yearbook_parameters, school_name=school_name,
                                         grade='PreK', classroom=None, child=None, parent_book=school_yearbook.pickle_yearbook)

        assert grade_yearbook.pickle_yearbook.parent_book.__repr__() == school_yearbook.__repr__()

    if __name__ == '__main__':
        unittest.main()
