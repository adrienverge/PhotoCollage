"""
This class will contain methods and interfaces that will operate on a processed corpus and retrieve a list of images
"""
from yearbook.Corpus import Corpus
from abc import ABC, abstractmethod


class ImageRanker(ABC):

    @abstractmethod
    def __init__(self, corpus: Corpus):
        self.corpus = corpus

    @abstractmethod
    def rank(self, school: str, grade: str, classroom: str, child: str, event_name: str) -> [str]:
        pass

    @abstractmethod
    def whoamI(self):
        pass


class SchoolRanker(ImageRanker):
    def __init__(self, corpus: Corpus):
        self.corpus = corpus
        self.school_name = "Unknown"

    def __init__(self, corpus: Corpus, school_name: str):
        super(SchoolRanker, self).__init__(corpus)
        self.school_name = school_name

    def rank(self, school: str, grade: str, classroom: str, child: str, event_name: str) -> [str]:
        # Return a list of images that are applicable to the school level
        return self.corpus.get_filenames_for_event_images(event_name)

    def whoamI(self):
        print("SchoolRanker, %s" % self.school_name)


class GradeRanker(ImageRanker):
    def __init__(self, corpus: Corpus):
        self.corpus = corpus

    def rank(self, school: str, grade: str, classroom: str, child: str, event_name: str) -> [str]:
        # Return a list of images that are applicable to the grade level
        return self.corpus.get_filenames_for_event_images(event_name)

    def whoamI(self):
        print("GradeRanker")


class ClassroomRanker(ImageRanker):
    def __init__(self, corpus: Corpus):
        self.corpus = corpus

    def rank(self, school: str, grade: str, classroom: str, child: str, event_name: str) -> [str]:
        # Return a list of images that are applicable to the classroom level
        return self.corpus.get_filenames_for_event_images(event_name)

    def whoamI(self):
        print("ClassRoomRanker")


class ChildRanker(ImageRanker):
    def __init__(self, corpus: Corpus):
        self.corpus = corpus

    def rank(self, school: str, grade: str, classroom: str, child: str, event_name: str) -> [str]:
        # Return a list of images that are applicable to the child
        return self.corpus.get_filenames_child_images_for_event(child, event_name)

    def whoamI(self):
        print("ChildRanker")
