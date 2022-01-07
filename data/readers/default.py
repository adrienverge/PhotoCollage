from yearbook.Corpus import Corpus
from yearbook.Photograph import Photograph

from util.utils import get_box_from_points_arr


def corpus_processor(school_name: str, corpus_file: str = None, tag_file: str = None) -> {}:
    face_to_image_map = {}
    event_to_image_map = {}  # For a given event, we can track the images

    all_images_map = {}

    # Corpus files are stored in GoogleDrive/ProcessedCorpus
    import os
    import getpass

    if corpus_file is None:
        corpus_file = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', 'ProcessedCorpus', school_name + ".out")

    image_to_tag_map = {}
    if tag_file is None:
        tag_file_path = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', 'ProcessedCorpus', school_name + "_tags.out")
        if os.path.exists(tag_file_path):
            tag_file = tag_file_path

    if tag_file is not None:

        print("We found a tag file for this school at %s " % tag_file)
        # we have no tags to add to the images...
        # need to know what the default is going to be
        with open(tag_file, 'r') as reader:
            for line in reader.readlines():
                values = line.split("\t")
                img_name = values[0]
                tags_list = values[1]

                # For the time being, we're going to add the full image name as key and string of tags as values
                image_to_tag_map[img_name] = tags_list

        print("We've got tags for %s images " % str(len(image_to_tag_map)))

    # read the corpus file
    with open(corpus_file, 'r') as reader:
        for line in reader.readlines():
            values = line.split("\t")
            img_name = values[0]
            # faces is given as child_name:score:bounding_box_dimensions
            # Bounding box dimensions are provided in this format,
            # left=938.17993, top=651.6867, right=1033.7305, bottom=777.44586

            # currently, first value is name of child, second is the confidence score, and third is the face bounding
            # box
            faces = list(map(lambda x: (x.split(":")[0], x.split(":")[1],
                                        get_box_from_points_arr(x.split(":")[2].split(","))), values[1].split(";")))
            event_name = values[2].strip()
            corpus_image = Photograph(img_name, faces, event_name)
            face_to_image = {face[0]: [(img_name, face[1], face[2])] for face in faces}

            for face in face_to_image:
                if face in face_to_image_map:
                    face_to_image_map[face].extend(face_to_image[face])
                else:
                    face_to_image_map[face] = face_to_image[face]

            if event_name in event_to_image_map:
                event_to_image_map[event_name].append(img_name)
            else:
                event_to_image_map[event_name] = [img_name]

            all_images_map[corpus_image.name] = corpus_image

    # at the end lets sort this whole list by the best matches
    for face in face_to_image_map:
        imgs = face_to_image_map[face]
        sorted_images = sorted(imgs, key=lambda x: x[1], reverse=True)
        face_to_image_map[face] = sorted_images

    import os
    corpus_dir = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', school_name)

    return Corpus(school_name=school_name, image_map=all_images_map, child_to_images=face_to_image_map,
                  events_to_images=event_to_image_map,
                  image_tags=image_to_tag_map,
                  corpus_dir=corpus_dir)
