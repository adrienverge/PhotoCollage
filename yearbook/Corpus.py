def get_portrait_images_for_child(drive_dir, school_name, child):
    import os
    images_per_child = []

    try:
        selfie_dir = os.path.join(drive_dir, school_name, "Selfies", child)
        images_per_child = [os.path.join(selfie_dir, image) for image in os.listdir(selfie_dir)
                            if image.endswith("jpg")]
    except:
        pass

    return images_per_child


def intersection(lst1, lst2):
    # Use of hybrid method
    temp = set(lst2)
    lst3 = [value for value in lst1 if value in temp]
    return lst3


class Corpus:

    def __init__(self, school_name: str, image_to_tags: {}, tags_to_images: {}, image_to_faces: {}, corpus_dir: str):
        self.school_name = school_name
        self.image_to_tags = image_to_tags
        self.tags_to_images = tags_to_images
        self.image_to_faces = image_to_faces
        self.corpus_dir = corpus_dir

    def get_images_for_child(self, tags_list: [str], child_name: str) -> [str]:
        images = self.get_images_with_tags(tags_list)
        child_imgs = []

        # Only keep the ones that have a face detected in there
        for img in images:
            faces = self.image_to_faces[img]
            if child_name in faces:
                child_imgs.append(img)

        return child_imgs

    def get_images_with_tags(self, tags_list: [str]) -> [str]:
        # Get the images that have this given tags
        all_images = [self.tags_to_images[tag] for tag in tags_list if tag in self.tags_to_images]

        # Now all_images is [[img0, img1] [img3, img4] [img5] [img5] [img6]]
        # We need to return an intersection of the lists
        import functools
        try:
            final_images = functools.reduce(lambda x, y: intersection(x, y), all_images)
        except TypeError:
            final_images = []

        return final_images

    def get_images_with_tags_strict(self, tags_list: [str]) -> [str]:

        tag_list_len = len(tags_list)

        # Get the images that have this given tags
        all_images = [self.tags_to_images[tag] for tag in tags_list if tag in self.tags_to_images]

        # Now all_images is [[img0, img1] [img3, img4] [img5] [img5] [img6]]
        # We need to return an intersection of the lists
        import functools
        images_with_same_no_of_tags = []
        try:
            final_images = functools.reduce(lambda x, y: intersection(x, y), all_images)
            images_with_same_no_of_tags = [img for img in final_images if len(self.image_to_tags[img]) == tag_list_len]
            images_with_same_tags = []
            for img in final_images:
                img_tags = self.image_to_tags[img]
                common_tags = intersection(img_tags, tags_list)
                if len(common_tags) == len(img_tags):
                    images_with_same_tags.append(img)

        except TypeError:
            pass

        return images_with_same_tags

