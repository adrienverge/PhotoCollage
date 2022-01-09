import unittest

from data.sqllite.reader import get_tree_model, get_album_details_for_school
import getpass
import os


def print_row(store, treepath, treeiter):
    print("\t" * (treepath.get_depth() - 1), store[treeiter][:], sep="")


class TestReader(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(TestReader, self).__init__(*args, **kwargs)
        self.output_base_dir = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', 'YearbookCreatorOut')
        self.yearbook_parameters = {'max_count': 12,
                                    'db_file_path': os.path.join(self.output_base_dir, 'RY.db'),
                                    'output_dir': os.path.join(self.output_base_dir, getpass.getuser()),
                                    'corpus_base_dir': os.path.join('/Users', getpass.getuser(), 'GoogleDrive',
                                                                    'Monticello_Preschool_2021_2022')}

    def test_create_tree_model_per_school(self):
        tree_model = get_tree_model(self.yearbook_parameters,
                                    'Monticello_Preschool_2021_2022')
        print("Printing rows")
        tree_model.foreach(print_row)

    def test_get_album_details(self):
        album_details = get_album_details_for_school(self.yearbook_parameters['db_file_path'],
                                                     'Monticello_Preschool_2021_2022')
        for row in album_details:
            print(row)


if __name__ == '__main__':
    unittest.main()
