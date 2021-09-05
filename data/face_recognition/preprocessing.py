from PIL import Image

# EXIF orientation info http://sylvana.net/jpegcrop/exif_orientation.html
exif_orientation_tag = 0x0112
exif_transpose_sequences = [  # Val  0th row  0th col
    [],  # 0    (reserved)
    [],  # 1   top      left
    [Image.FLIP_LEFT_RIGHT],  # 2   top      right
    [Image.ROTATE_180],  # 3   bottom   right
    [Image.FLIP_TOP_BOTTOM],  # 4   bottom   left
    [Image.FLIP_LEFT_RIGHT, Image.ROTATE_90],  # 5   left     top
    [Image.ROTATE_270],  # 6   right    top
    [Image.FLIP_TOP_BOTTOM, Image.ROTATE_90],  # 7   right    bottom
    [Image.ROTATE_90],  # 8   left     bottom
]


class ExifOrientationNormalize(object):
    """
    Normalizes rotation of the image based on exif orientation info (if exists.)
    """

    def __call__(self, img):
        if 'parsed_exif' in img.info and exif_orientation_tag in img.info['parsed_exif']:
            orientation = img.info['parsed_exif'][exif_orientation_tag]
            transposes = exif_transpose_sequences[orientation]
            for trans in transposes:
                img = img.transpose(trans)
        return img


class Whitening(object):
    """
    Whitens the image.
    """

    def __call__(self, img):
        mean = img.mean()
        std = img.std()
        std_adj = std.clamp(min=1.0 / (float(img.numel()) ** 0.5))
        y = (img - mean) / std_adj
        return y
