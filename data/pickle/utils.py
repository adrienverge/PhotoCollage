import pickle, os
from pathlib import Path

from yearbook.Yearbook import Yearbook


def store_yearbook(yearbook: Yearbook, filename: str):
    path1 = Path(filename)
    # Create the parent directories if they don't exist
    os.makedirs(path1.parent, exist_ok=True)

    # Important to open the file in binary mode
    with open(filename, 'wb') as f:
        pickle.dump(yearbook, f)


def load_pickled_yearbook(filename: str):
    pickle_file = open(filename, 'rb')
    yearbook = pickle.load(pickle_file)
    pickle_file.close()

    return yearbook


def pickle_path_for_child(output_dir:str, school_name: str, child_name: str):
    import os
    return os.path.join(output_dir, ".pickle", school_name, child_name + ".pickle")

