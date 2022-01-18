import unittest, random
from data.readers.default import corpus_processor
from yearbook.Corpus import intersection


class TestDefaultReader(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(TestDefaultReader, self).__init__(*args, **kwargs)
        self.corpus = corpus_processor(school_name='Monticello_Preschool_2021_2022')

    def test_monticello_corpus_with_tags(self):
        print(len(self.corpus.image_to_tags))
        assert len(self.corpus.image_to_tags) >= 2099
        image_tags = self.corpus.image_to_tags[
            '/Users/ashah/GoogleDrive/Monticello_Preschool_2021_2022/Halloween/IMG_5811.png']
        assert "Halloween" in image_tags
        print(image_tags)
        assert len(image_tags) == 3

    def test_monticello_corpus_images_for_event(self):
        images = self.corpus.tags_to_images['Portraits']
        assert len(images) >= 328
        assert images.index(
            '/Users/ashah/GoogleDrive/Monticello_Preschool_2021_2022/Adventureland/Portraits/Ethan Tang_2.png') >= 1

    def test_get_child_portraits(self):
        tags_list = ["Portraits",
                     "PreK",
                     "Jungle",
                     "Laura Sun"]
        lauraImages = self.corpus.get_images_with_tags_strict(tags_list)
        print(len(lauraImages))
        [print(img) for img in lauraImages]

    def test_longer_lists(self):
        tags_list = ["Sunshine",
                     "Portraits",
                     "Monticello_Preschool_2021_2022",
                     "PreK",
                     "Adventureland",
                     "Aarish Mathur"]

        assert len(self.corpus.get_images_with_tags_strict(tags_list)) == 0

    def test_get_images(self):
        sunshine_portraits = self.corpus.get_images_with_tags_strict(["Monticello_Preschool_2021_2022",
                                                                  "PreK", "Portraits", "Sunshine"])
        adventure_portraits = self.corpus.get_images_with_tags_strict(["Portraits", "Adventureland"])
        assert len(sunshine_portraits) >= 50
        assert len(adventure_portraits) >= 50

        assert len(sunshine_portraits) != len(adventure_portraits)

        assert len(intersection(sunshine_portraits, adventure_portraits)) == 0

    def test_get_images_for_portraits(self):
        assert len(self.corpus.get_portraits(grade="PreK", classroom="Seaturtle", child="Emily Lin")) == 5
        assert len(self.corpus.get_portraits(grade="PreK", classroom="Seaturtle", child="Finn Yao")) == 7

        # Also test with PreK tag as that's the default tag for all images
        assert len(self.corpus.get_portraits(classroom="Seaturtle", grade="PreK", child="Finn Yao")) == 7

        tag_list = ["Portraits", "PreK", "Seaturtle", "Finn Yao"]
        child_portraits = self.corpus.get_images_with_tags_strict(tag_list)
        assert len(child_portraits) == 7


if __name__ == '__main__':
    unittest.main()
