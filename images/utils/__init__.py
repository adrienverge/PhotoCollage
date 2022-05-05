from PIL import Image


def get_date_taken(path):
    print("Looking for date for %s " % path)
    exif = Image.open(path)._getexif()
    if exif is not None:
        return get_minimum_creation_time(exif)

    return None


def get_date(img):
    return img._getexif()[36867]


def get_minimum_creation_time(exif_data):
    mtime = "?"
    if 306 in exif_data and exif_data[306] < mtime: # 306 = DateTime
        mtime = exif_data[306]
    if 36867 in exif_data and exif_data[36867] < mtime: # 36867 = DateTimeOriginal
        mtime = exif_data[36867]
    if 36868 in exif_data and exif_data[36868] < mtime: # 36868 = DateTimeDigitized
        mtime = exif_data[36868]
    return mtime


def get_orientation_fixed_pixbuf(img_name: str, width=120, height=120):
    import PIL
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GdkPixbuf', '2.0')

    from gi.repository import GdkPixbuf
    pixbuf = None

    try:
        pil_image = PIL.Image.open(img_name)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=img_name,
            width=width,
            height=height,
            preserve_aspect_ratio=True)

        exif = pil_image._getexif()
        if exif is not None and 274 in exif:  # orientation tag
            orientation = exif[274]
            if orientation == 3:
                pixbuf = pixbuf.rotate_simple(180)
            elif orientation == 6:
                pixbuf = pixbuf.rotate_simple(270)
            elif orientation == 8:
                pixbuf = pixbuf.rotate_simple(90)
    except OSError:
        # raise BadPhoto(name)
        print("Skipping a photo: %s" % img_name)
        return None

    return pixbuf
