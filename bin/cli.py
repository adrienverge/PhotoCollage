import math
import os
import pathlib
import random
import argparse

from photocollage import render
from photocollage.collage import Page


def make_collage(output_filename, photos):
    # Define the output image height / width ratio
    ratio = 1.0 * out_h / out_w

    """
    Compute a good number of columns. It depends on the ratio, the number
    of images and the average ratio of these images. According to my
    calculations, the number of column should be inversely proportional
    to the square root of the output image ratio, and proportional to the
    square root of the average input images ratio.
    """
    avg_ratio = sum(
        1.0 * photo_from_list.h / photo_from_list.w for photo_from_list in
        photos) / len(photos)

    """
    Virtual number of images: since ~ 1 image over 3 is in a multi-cell
    (i.e. takes two columns), it takes the space of 4 images.
    So it's equivalent to 1/3 * 4 + 2/3 = 2 times the number of images.
    """
    virtual_no_images = 2 * len(photos)
    no_cols = int(round(math.sqrt(avg_ratio / ratio * virtual_no_images)))

    border_w = 0.01
    border_c = (0, 0, 0)  # black
    # border_c = render.random_color()

    page = Page(1.0, ratio, no_cols)
    random.shuffle(photos)
    for photo_from_list in photos:
        page.add_cell(photo_from_list)
    page.adjust()

    # If the desired ratio changed in the meantime (e.g. from landscape to
    # portrait), it needs to be re-updated
    page.target_ratio = 1.0 * out_h / out_w
    page.adjust_cols_heights()
    page.scale_to_fit(out_w, out_h)
    enlargement = float(out_w) / page.w
    page.scale(enlargement)

    t = render.RenderingTask(
        page, output_file=output_filename,
        border_width=border_w * max(page.w, page.h),
        border_color=border_c)

    t.start()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Make collages.')
    parser.add_argument('--files', type=str, nargs='+', dest='files',
                        help='a collection of files to use for the collage')
    parser.add_argument('--folder', type=str, dest='folder',
                        help='the folder to scan for files to use for the '
                             'collage')
    parser.add_argument('--outDir', '-D', dest='output_directory',
                        required=True,
                        help='the directory to output the files to')
    parser.add_argument('--recurse', '-r', dest='recurse', action='store_true',
                        help='recurse through the directory')
    parser.add_argument('-n', dest='amount', type=int, nargs='?',
                        help='the amount of collages to create', default=10,
                        const=10)
    parser.add_argument('--height', type=int, nargs='?',
                        help='the height of the collages', default=2160,
                        const=2160)
    parser.add_argument('--width', type=int, nargs='?',
                        help='the width of the collages', default=3840,
                        const=3840)
    parser.add_argument('--min', type=int, nargs='?',
                        help='the minimal number of images per collage',
                        default=3, const=3)
    parser.add_argument('--max', type=int, nargs='?',
                        help='the maximal number of images per collage',
                        default=15,
                        const=15)
    parser.add_argument('--max-ratio', type=float, nargs='?', dest='max_ratio',
                        default=1.5, const=1.5,
                        help='the maximal width over height ratio that is '
                             'allowed for photos in the collage')

    args = parser.parse_args()

    out_h = args.height
    out_w = args.width

    if not os.path.isdir(args.output_directory):
        print("The output directory '" + args.output_directory +
              "' is not a directory.")
        exit(-1)

    output_directory = str(pathlib.Path(args.output_directory).absolute())

    filenames = []
    if (not (args.files is None)) and len(args.files) > 0:
        filenames.extend(args.files)

    if len(args.folder) != 0:
        if args.recurse:
            for dir_path, dirs, files in os.walk(args.folder):
                for file in files:
                    filename, file_extension = os.path.splitext(file)
                    if file_extension in (
                            ".png", ".PNG", ".jpg", ".JPG", ".jpeg", ".JPEG"):
                        filenames.append(os.path.join(dir_path, file))
            for entry in os.scandir(args.folder):
                if entry.is_file():
                    filename, file_extension = os.path.splitext(entry.name)
                    if file_extension in (
                            "png", "PNG", "jpg", "JPG", "jpeg", "JPEG"):
                        filenames.append(entry.name)

    photo_list = render.build_photolist(filenames)

    for photo in photo_list:
        if float(photo.w) / float(photo.h) > args.max_ratio:
            photo_list.remove(photo)

    if len(filenames) == 0:
        print("No images found.")
        exit(-1)

    i = 0
    counter = 0

    while i < args.amount:
        random.shuffle(photo_list)
        number_of_images = random.randint(args.min, args.max)

        found_unused_filename = False
        filename = ""

        while not found_unused_filename:
            counter += 1
            filename = os.path.join(output_directory,
                                    "collage - " + str(counter) + ".jpg")
            found_unused_filename = not os.path.exists(filename)

        make_collage(filename, photo_list[0:number_of_images])
        i += 1
