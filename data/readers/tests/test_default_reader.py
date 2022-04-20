import getpass
import unittest
from data.readers.default import corpus_processor
from yearbook.Corpus import intersection
import os


class TestDefaultReader(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(TestDefaultReader, self).__init__(*args, **kwargs)
        self.school_name = 'Monticello_Preschool_2021_2022'
        self.user_name = getpass.getuser()

        self.school_base_dir = os.path.join("/Users", self.user_name, "GoogleDrive", self.school_name)
        self.corpus = corpus_processor(school_name=self.school_name)

    def test_monticello_corpus_with_tags(self):
        assert len(self.corpus.image_to_tags) >= 2099
        import os

        username = getpass.getuser()
        file_path = os.path.join(self.school_base_dir, 'HalloweenParade')
        image_tags = self.corpus.image_to_tags[
            file_path + '/IMG_5352.png']
        assert "HalloweenParade" in image_tags
        assert self.school_name in image_tags
        assert len(image_tags) == 2

    def test_monticello_corpus_images_for_event(self):
        images = self.corpus.tags_to_images['SunshinePortraits']
        assert len(images) >= 119
        known_portrait1 = os.path.join(self.school_base_dir, "SunshinePortraits", "Shivank Jithin_1.png")
        known_portrait2 = os.path.join(self.school_base_dir, "SunshinePortraits", "Tingyu Deng_1.png")

        assert images.index(
            known_portrait1) >= 1

        assert images.index(
            known_portrait2) >= 1

    def test_get_child_portraits(self):
        child_name = "Laura Sun"
        class_name = "JunglePortraits"
        tags_list = [child_name, class_name]
        child_images = self.corpus.get_images_with_tags_strict(tags_list)
        assert len(child_images) == 2

    def test_longer_lists_1(self):
        tags_list = ['Classroom', 'VargasElementary', 'Grade4_Herron']
        corpus = corpus_processor(school_name="VargasElementary")
        assert len(corpus.get_images_with_tags_strict(tags_list)) == 0


    def test_longer_lists(self):
        tags_list = ["Sunshine",
                     "Portraits",
                     "Monticello_Preschool_2021_2022",
                     "Adventureland",
                     "Aarish Mathur"]

        assert len(self.corpus.get_images_with_tags_strict(tags_list)) == 0

        tags_list = ['Monticello_Preschool_2021_2022', 'LadybugsPortraits', 'Aahana Namjoshi']

        assert 5 == len(self.corpus.get_images_for_child(tags_list, 'Aahana Namjoshi'))
        for img in self.corpus.get_images_for_child(tags_list, 'Aahana Namjoshi'):
            assert 'LadybugsPortraits' in img

    def test_get_images(self):
        sunshine_portraits = self.corpus.get_images_with_tags_strict([
            "Monticello_Preschool_2021_2022", "SunshinePortraits"])
        adventure_portraits = self.corpus.get_images_with_tags_strict(["Monticello_Preschool_2021_2022", "AdventurelandPortraits"])
        print("adventure_portraits portraits %s" % str(len(adventure_portraits)))
        assert len(sunshine_portraits) >= 77
        assert len(adventure_portraits) >= 9

        assert len(sunshine_portraits) != len(adventure_portraits)

        assert len(intersection(sunshine_portraits, adventure_portraits)) == 0


if __name__ == '__main__':
    unittest.main()
