from reportlab.lib.units import inch


class CoverSettings:
    def get_page_size(self):
        pass

    def get_top_left_back_cover(self):
        return 0.75 * inch, 0.75 * inch

    def get_top_left_front_cover(self):
        pass

    def get_cover_img_dims(self):
        pass


class HardCoverSettings(CoverSettings):

    def get_page_size(self):
        return 19 * inch, 12.75 * inch

    def get_cover_img_dims(self):
        width = 8.625 * inch
        height = 11.25 * inch
        return width, height

    def get_top_left_front_cover(self):
        x = 9.625 * inch
        y = 0.75 * inch
        return x, y


class SoftCoverSettings(CoverSettings):
    def get_page_size(self):
        return 17.38 * inch, 11.25 * inch

    def get_cover_img_dims(self):
        width = 8.5 * inch
        height = 11 * inch
        return width, height

    def get_top_left_front_cover(self):
        x = 9.625 * inch
        y = 0.75 * inch
        return x, y


def get_cover_settings(cover_format: str) -> CoverSettings:
    print("Returning cover setting for %s " % cover_format)
    if cover_format == "HardCover" or cover_format == "Hardcover" or cover_format == "hardcover":
        return HardCoverSettings()
    elif cover_format == "SoftCover" or cover_format == "Softcover" or cover_format == "softcover":
        return SoftCoverSettings()
    elif cover_format == "Digital" or cover_format == "digital":
        return None
    else:
        raise ValueError(cover_format)
