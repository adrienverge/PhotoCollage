import unittest

from data.sqllite.reader import get_tree_model


def print_row(store, treepath, treeiter):
    print("\t" * (treepath.get_depth() - 1), store[treeiter][:], sep="")


class TestReader(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(TestReader, self).__init__(*args, **kwargs)

    def test_create_tree_model_per_school(self):
        import getpass
        import os
        self.output_base_dir = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', 'YearbookCreatorOut')
        yearbook_parameters = {'max_count': 12,
                               'db_file_path': os.path.join(self.output_base_dir, 'RY.db'),
                               'output_dir': os.path.join(self.output_base_dir, getpass.getuser())}

        tree_model = get_tree_model(yearbook_parameters,
                                    'Appleseed_2018_2019')
        print("Printing rows")
        tree_model.foreach(print_row)


if __name__ == '__main__':
    unittest.main()
