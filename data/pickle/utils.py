def get_dir_path(output_dir: str, school_name: str, classroom: str, child_name: str, direc_name:str):
    import os
    if classroom is None:
        pickle_file_path = os.path.join(output_dir, "." + direc_name, school_name + "_" + direc_name)
    elif child_name is None:
        pickle_file_path = os.path.join(output_dir, "." + direc_name, school_name, classroom + "_" + direc_name)
    else:
        pickle_file_path = os.path.join(output_dir, "." + direc_name, school_name, classroom, child_name + "_" + direc_name)

    # we will make the directory for now
    os.makedirs(pickle_file_path, exist_ok=True)
    return pickle_file_path


def get_pickle_path(output_dir: str, school_name: str, classroom: str, child_name: str):
    return get_dir_path(output_dir, school_name, classroom, child_name, "pickle")


def get_jpg_path(output_dir: str, school_name: str, classroom: str, child_name: str):
    return get_dir_path(output_dir, school_name, classroom, child_name, "jpgs")


def get_pdf_path(output_dir: str, school_name: str, classroom: str, child_name: str):
    return get_dir_path(output_dir, school_name, classroom, child_name, "pdfs")

