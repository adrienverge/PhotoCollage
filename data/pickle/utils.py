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


def get_dir_path(output_dir: str, school_name: str, grade: str, classroom: str, child_name: str, direc_name:str):
    import os
    if grade is None:
        pickle_file_path = os.path.join(output_dir, ".", direc_name, school_name + "." + direc_name)
    elif classroom is None:
        pickle_file_path = os.path.join(output_dir, ".", direc_name, school_name, grade + "." + direc_name)
    elif child_name is None:
        pickle_file_path = os.path.join(output_dir, ".", direc_name, school_name, grade, classroom + "." + direc_name)
    else:
        pickle_file_path = os.path.join(output_dir, ".", direc_name, school_name, grade, classroom, child_name + "." + direc_name)

    # we will make the directory for now
    os.makedirs(pickle_file_path, exist_ok=True)
    return pickle_file_path


def get_pickle_path(output_dir: str, school_name: str, grade: str, classroom: str, child_name: str):
    return get_dir_path(output_dir, school_name, grade, classroom, child_name, "pickle")


def get_jpg_path(output_dir: str, school_name: str, grade: str, classroom: str, child_name: str):
    return get_dir_path(output_dir, school_name, grade, classroom, child_name, "jpg")


def get_pdf_path(output_dir: str, school_name: str, grade: str, classroom: str, child_name: str):
    return get_dir_path(output_dir, school_name, grade, classroom, child_name, "pdf")

