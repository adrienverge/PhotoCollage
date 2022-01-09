"""
This class will contain methods and interfaces that will operate on a processed corpus and retrieve a list of images
"""
from abc import ABC, abstractmethod

from util.utils import get_unique_list_insertion_order
from yearbook.Corpus import Corpus
from yearbook.Yearbook import Yearbook
from yearbook.page.Page import Page


def get_parent_page_images(yearbook: Yearbook, current_page:Page):
    # this is our fallback, we need to return the images that made it on the parent yearbook, same page
    print("Returning images that were part of the parent book")
    parent_page: Page = yearbook.pickle_yearbook.parent_book.pages[current_page.number-1]
    return parent_page.photos_on_page


class ImageRanker(ABC):

    @abstractmethod
    def __init__(self, corpus: Corpus):
        self.corpus = corpus

    @abstractmethod
    def rank(self, yearbook: Yearbook, current_page: Page) -> [str]:
        pass

    def get_candidate_images(self, yearbook: Yearbook, current_page: Page, max_count: int = 12) -> [str]:
        if not current_page.personalized:
            print("Load image as is, %s, %s" % (current_page.event_name, current_page.image))
            return [current_page.image]

        prev_page: Page = yearbook.get_prev_page(current_page)

        print("Calling rank for %s, %s" % (current_page.event_name, current_page.image))
        # First rank all candidate images
        all_images = self.rank(yearbook, current_page)

        # Then remove all the images from the previous page
        if prev_page.number == current_page.number:
            novel_images = all_images
        else:
            novel_images = [img for img in all_images if img not in prev_page.photos_on_page]

        if len(novel_images) < max_count:
            # We have very few images for this page...
            # we probably should save some for the next page
            novel_images = novel_images[:max(int(len(novel_images)/2), 1)]

        # Then lets get the parent pinned images as they have to be there on the page
        _pinned_photos = current_page.get_all_pinned_photos()
        _pinned_photos.extend(novel_images[:max_count])

        final_list = get_unique_list_insertion_order(_pinned_photos)

        if final_list is None or len(final_list) == 0:
            print("LAST RESORT HACK FOR THE TIME BEING")
            import os
            import getpass
            final_list = [os.path.join("/Users", getpass.getuser(), 'GoogleDrive', yearbook.school, 'blank.png')]

        return final_list

    @abstractmethod
    def who_am_i(self):
        pass


class SchoolRanker(ImageRanker):
    def __init__(self, corpus: Corpus):
        self.corpus = corpus
        self.school_name = "Unknown"

    def __init__(self, corpus: Corpus, school_name: str):
        super(SchoolRanker, self).__init__(corpus)
        self.school_name = school_name

    def rank(self, yearbook: Yearbook, current_page: Page) -> [str]:
        # Return a list of images that are applicable to the grade level
        tag_list = []
        tag_list.extend(current_page.tags.split(","))
        tag_list.append(current_page.event_name)
        tag_list.append(yearbook.school)

        # Return a list of images that are applicable to the school and page tags
        # This can never be None as all images are eligible for school level pages
        images = self.corpus.get_intersection_images(tag_list)
        if images is None or len(images) == 0:
            images = get_parent_page_images(yearbook, current_page)

        return images

    def who_am_i(self):
        print("SchoolRanker, %s" % self.school_name)


class GradeRanker(ImageRanker):
    def __init__(self, corpus: Corpus):
        self.corpus = corpus

    def rank(self, yearbook: Yearbook, current_page: Page) -> [str]:
        # Return a list of images that are applicable to the grade level
        tag_list = []

        # Original page tags are a string, we need to split to make it a list
        tag_list.extend(current_page.tags.split(","))
        tag_list.append(current_page.event_name)
        tag_list.append(yearbook.school)
        tag_list.append(yearbook.grade)

        # Return a list of images that are applicable to the grade
        images = self.corpus.get_intersection_images(tag_list)

        if images is None or len(images) == 0:
            images = get_parent_page_images(yearbook, current_page)

        return images

    def who_am_i(self):
        print("GradeRanker")


class ClassroomRanker(ImageRanker):
    def __init__(self, corpus: Corpus):
        self.corpus = corpus

    def rank(self, yearbook: Yearbook, current_page: Page) -> [str]:
        tag_list = []
        tag_list.extend(current_page.tags.split(","))
        tag_list.append(current_page.event_name)
        tag_list.append(yearbook.school)
        tag_list.append(yearbook.grade)
        tag_list.append(yearbook.classroom)

        # Return a list of images that are applicable to the classroom
        images = self.corpus.get_intersection_images(tag_list)

        if images is None or len(images) == 0:
            images = get_parent_page_images(yearbook, current_page)

        return images

    def who_am_i(self):
        print("ClassRoomRanker")


class ChildRanker(ImageRanker):
    def __init__(self, corpus: Corpus):
        self.corpus = corpus

    def rank(self, yearbook: Yearbook, current_page: Page) -> [str]:
        tag_list = []
        tag_list.extend(current_page.tags.split(","))
        tag_list.append(current_page.event_name)
        tag_list.append(yearbook.school)
        tag_list.append(yearbook.grade)
        tag_list.append(yearbook.classroom)
        tag_list.append(yearbook.child)

        # Return a list of images that are applicable to the child
        # There's a good possibility that this is None
        images = self.corpus.get_intersection_images(tag_list)
        if images is None or len(images) == 0:
            images = get_parent_page_images(yearbook, current_page)

        return images

    def who_am_i(self):
        print("ChildRanker")
