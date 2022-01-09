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

    def __init__(self, school_name: str, image_to_tags: {}, tags_to_images: {}, corpus_dir: str):
        self.school_name = school_name
        self.image_to_tags = image_to_tags
        self.tags_to_images = tags_to_images
        self.corpus_dir = corpus_dir

    def get_image_tags(self, img_full_path: str) -> str:
        if img_full_path in self.image_tags:
            return self.image_tags[img_full_path]
        else:
            return "Unknown"

    def get_intersection_images(self, tags_list: [str]) -> [str]:

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

    def get_portraits(self, grade: str, classroom: str, child: str):
        portrait_images = [img for img in self.tags_to_images[child] if "Portraits" in self.image_to_tags[img]
                           and classroom in self.image_to_tags[img]
                           and grade in self.image_to_tags[img]]

        if portrait_images is None or len(portrait_images) == 0:
            # Need a default image being returned here
            print("Some default image needs to be returned")

        return portrait_images
