import os
from yearbook.page import Page


def read_files_from_dir(directory):
    return [os.path.join(directory, p) for p in sorted(os.listdir(directory)) if not p.startswith(".")]


def read_student_names_from_dir(directory):
    return [p for p in sorted(os.listdir(directory)) if not p.startswith(".")]


def read_page_template(directory):
    return [Page.read_page_json(os.path.join(directory, p)) for p in sorted(os.listdir(directory)) if
            p.endswith('.json')]

