import unittest
from data.readers.default import corpus_processor
from yearbook.Corpus import intersection


class TestDefaultReader(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(TestDefaultReader, self).__init__(*args, **kwargs)
        self.corpus = corpus_processor(school_name='Monticello_Preschool_2021_2022')

    def test_monticello_corpus_with_tags(self):
        assert len(self.corpus.image_to_tags) >= 2099
        image_tags = self.corpus.image_to_tags[
            '/Users/ashah/GoogleDrive/Monticello_Preschool_2021_2022/Halloween/IMG_5882.png']
        assert "Halloween" in image_tags
        assert len(image_tags) == 2

    def test_monticello_corpus_images_for_event(self):
        images = self.corpus.tags_to_images['Portraits']
        print(len(images))
        assert len(images) >= 311
        assert images.index(
            '/Users/ashah/GoogleDrive/Monticello_Preschool_2021_2022/Adventureland/Portraits/Vidya Iyengar_5.png') >= 1

    def test_get_child_portraits(self):
        tags_list = ["Portraits",
                     "Jungle",
                     "Laura Sun"]
        lauraImages = self.corpus.get_images_with_tags_strict(tags_list)
        print(len(lauraImages))
        [print(img) for img in lauraImages]

    def test_longer_lists(self):
        tags_list = ["Sunshine",
                     "Portraits",
                     "Monticello_Preschool_2021_2022",
                     "Adventureland",
                     "Aarish Mathur"]

        assert len(self.corpus.get_images_with_tags_strict(tags_list)) == 0

        tags_list = ['Monticello_Preschool_2021_2022', 'Ladybugs', 'Portraits', 'Aahana Namjoshi']
        print("**********")
        [print(img) for img in self.corpus.get_images_with_tags_strict(tags_list)]
        print("**********")
        [print(img) for img in self.corpus.get_images_for_child(tags_list, 'Aahana Namjoshi')]

        print (self.corpus.image_to_tags["/Users/ashah/GoogleDrive/Monticello_Preschool_2021_2022/Ladybugs/Portraits/Aahana Namjoshi_4.png"])

    def test_get_images(self):
        sunshine_portraits = self.corpus.get_images_with_tags_strict([
            "Monticello_Preschool_2021_2022", "Portraits", "Sunshine"])
        adventure_portraits = self.corpus.get_images_with_tags_strict(["Monticello_Preschool_2021_2022", "Portraits", "Adventureland"])
        print("adventure_portraits portraits %s" % str(len(adventure_portraits)))
        assert len(sunshine_portraits) >= 125
        assert len(adventure_portraits) >= 27

        assert len(sunshine_portraits) != len(adventure_portraits)

        assert len(intersection(sunshine_portraits, adventure_portraits)) == 0

    def test_get_images_for_portraits(self):
        assert len(self.corpus.get_portraits(classroom="Seaturtle", child="Emily Lin")) == 3
        assert len(self.corpus.get_portraits(classroom="Seaturtle", child="Finn Yao")) == 3

        tag_list = ["Portraits", "Seaturtle", "Finn Yao"]
        child_portraits = self.corpus.get_images_with_tags_strict(tag_list)
        assert len(child_portraits) == 3


if __name__ == '__main__':
    unittest.main()
