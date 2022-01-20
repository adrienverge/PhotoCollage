from yearbook.Corpus import Corpus
from util.utils import get_box_from_points_arr


def corpus_processor(school_name: str, corpus_file: str = None, default_tags=None) -> Corpus:

    # Corpus files are stored in GoogleDrive/ProcessedCorpus
    if default_tags is None:
        default_tags = []

    import os
    import getpass
    image_to_tag_map: dict[str, list[str]] = {}
    tag_to_image_map: dict[str, list[str]] = {}

    if corpus_file is None:
        corpus_file = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', 'ProcessedCorpus', school_name + "_full.out")
        if os.path.exists(corpus_file):
            base_dir = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', school_name)
            # read the corpus file
            with open(corpus_file, 'r') as reader:
                for line in reader.readlines():
                    values = line.split("\t")
                    img_name = os.path.join(base_dir, values[0].strip())
                    # faces is given as child_name:score:bounding_box_dimensions
                    # Bounding box dimensions are provided in this format,
                    # left=938.17993, top=651.6867, right=1033.7305, bottom=777.44586

                    # currently, first value is name of child, second is the confidence score,
                    # and third is the face bounding
                    # box
                    faces = list(map(lambda x: (x.split(":")[0], x.split(":")[1],
                                                get_box_from_points_arr(x.split(":")[2].split(","))), values[1].split(";")))

                    # Event name is also another tag
                    tags = values[2].strip().split(",")
                    tags = [tag.strip() for tag in tags]
                    tags.extend(default_tags)
                    image_to_tag_map[img_name] = tags

                    for tag in tags:
                        if tag in tag_to_image_map:
                            tag_to_image_map[tag].append(img_name)
                        else:
                            tag_to_image_map[tag] = [img_name]

                    # corpus_image = Photograph(img_name, faces, event_name)
                    face_to_image = {face[0]: [(img_name, face[1], face[2])] for face in faces}

                    for face in face_to_image:
                        face = face.strip()
                        if face in tag_to_image_map:
                            tag_to_image_map[face].append(img_name)
                        else:
                            tag_to_image_map[face] = [img_name]

    corpus_dir = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', school_name)

    return Corpus(school_name=school_name,
                  image_to_tags=image_to_tag_map,
                  tags_to_images=tag_to_image_map,
                  corpus_dir=corpus_dir)
