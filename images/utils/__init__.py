from PIL import Image


def pixbuf2image(pix):
    """Convert gdkpixbuf to PIL image"""
    data = pix.get_pixels()
    w = pix.props.width
    h = pix.props.height
    stride = pix.props.rowstride
    mode = "RGB"
    if pix.props.has_alpha:
        mode = "RGBA"
    im = Image.frombytes(mode, (w, h), data, "raw", mode, stride)
    return im


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

    return pixbuf
