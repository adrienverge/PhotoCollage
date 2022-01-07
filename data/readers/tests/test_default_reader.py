import unittest, random
from data.readers.default import corpus_processor


class TestDefaultReader(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        print('BasicTest.__init__')
        super(TestDefaultReader, self).__init__(*args, **kwargs)
        self.corpus = corpus_processor('appleseed', './processedCorpus.test')

    def test_faces_in_image(self):
        photograph = self.corpus.image_map['1jT1b017LNxXFNKfOTmtF-i1LGvmiMxvt.jpg']
        assert len(photograph.faces) == 4

    def test_events_to_images(self):
        _images_per_event = self.corpus.events_to_images['Outdoor_Play']
        img_picked = random.choice(_images_per_event)
        print(img_picked)

    def test_corpus_total_lines_read(self):
        assert self.corpus.events_to_images['Outdoor_Play'] is not None
        assert len(self.corpus.child_to_images['Elise']) == 252
        assert len(self.corpus.get_child_images_for_event('Elise', 'Front_Cover')) == 3
        print(self.corpus.get_child_images_for_event('Elise', 'Front_Cover'))

    def test_corpus_with_scores(self):
        print("Running Test with scores")

        assert self.corpus.get_child_images_for_event_with_scores('Elise', 'Front_Cover') is not None
        assert len(self.corpus.get_child_images_for_event_with_scores('Elise', 'Front_Cover')) == 3
        print(self.corpus.get_child_images_for_event_with_scores('Elise', 'Front_Cover'))
        print(self.corpus.get_child_images_for_event_with_scores('Elisah', 'Front_Cover'))

    def test_face_bounding_box(self):
        print("Running Test with scores")

        assert len(self.corpus.image_map['159l0rWYaYxKHCTvvogdNoGN0BoU2ydYe.jpg'].faces) == 3

    def test_get_images_with_face_count(self):

        assert len(self.corpus.get_images_with_face_count(1)) == 332
        assert len(self.corpus.get_images_with_face_count(2)) == 161
        assert len(self.corpus.get_images_with_face_count(3)) == 116
        assert len(self.corpus.get_images_with_face_count(4)) == 108

    def test_children_in_corpus(self):
        assert(len(self.corpus.get_children())) == 21

    def test_get_filenames_child_images_for_event(self):
        corpus = corpus_processor('appleseed', './processedCorpus_2.test')
        christmas_imgs_per_child1 = corpus.get_filenames_child_images_for_event("Rilee", "Christmas")
        christmas_imgs_per_child2 = corpus.get_filenames_child_images_for_event("child3", "Christmas")
        christmas_imgs_per_unknown = corpus.get_filenames_child_images_for_event("asdfasdf", "Portraits")
        print(christmas_imgs_per_unknown)
        assert len(christmas_imgs_per_child1) == 6
        assert len(christmas_imgs_per_child2) == 2
        assert len(christmas_imgs_per_unknown) == 11

    def test_google_drive_corpus(self):
        corpus = corpus_processor(school_name='Appleseed_2018_2019')
        print(corpus.get_filenames_child_images_for_event('Ariya', 'Front_Cover'))

    def test_get_filenames_for_event_images(self):
        corpus = corpus_processor(school_name='Appleseed_2018_2019')
        print(corpus.get_filenames_for_event_images('Portraits'))

    def test_monticello_corpus_with_tags(self):
        corpus = corpus_processor(school_name='Monticello_Preschool_2021_2022')
        assert len(corpus.image_tags) >= 2161
        image_tags = corpus.image_tags['/Users/ashah/GoogleDrive/MonticelloPreschool2021_2022Master_PNGFiles' \
                                       '/Halloween/IMG_5352.png']
        assert "Halloween" in image_tags
        assert len(image_tags.split(",")) == 2

        print(corpus.events_to_images.keys())


if __name__ == '__main__':
    unittest.main()
