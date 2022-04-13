# Copyright (C) 2014 Adrien Vergé
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import random
from threading import Thread
import time

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFile
from PIL import ImageOps, ImageFont

from photocollage.collage import Photo
from photocollage.settings.PrintSettings import IMAGE_WITH_BLEED_SIZE, TEXT_FONT
from util.draw.DashedImageDraw import DashedImageDraw
from yearbook.page import Page

import os, getpass

QUALITY_SKEL = 0
QUALITY_FAST = 1
QUALITY_BEST = 2
# Hard Coded Size value of 8.75 by 11.25 inches

IMAGE_WITH_BLEED_SIZE = (2625, 3375)
FONT_DIR = os.path.join("/Users", getpass.getuser(), "GoogleDrive", "Fonts")
TEXT_FONT = ImageFont.truetype(os.path.join(FONT_DIR, "open-sans/OpenSans-Bold.ttf"), 100)
TEXT_FONT_SMALL = ImageFont.truetype(os.path.join(FONT_DIR, "open-sans/OpenSans-Bold.ttf"), 50)

# Try to continue even if the input file is corrupted.
# See issue at https://github.com/adrienverge/PhotoCollage/issues/65
PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True


class PIL_SUPPORTED_EXTS:
    """File extensions supported by PIL

    Compiled from:
    - http://pillow.readthedocs.org/en/2.3.0/handbook/image-file-formats.html
    - https://github.com/python-imaging/Pillow/blob/master/PIL/*ImagePlugin.py

    """
    RW = {
        "BMP": ("bmp",),
        # "EPS": ("ps", "eps",),   # doesn't seem to work
        "GIF": ("gif",),
        "IM": ("im",),
        "JPEG": ("jfif", "jpe", "jpg", "jpeg",),
        "MSP": ("msp",),
        "PCX": ("pcx",),
        "PNG": ("png",),
        "PPM": ("pbm", "pgm", "ppm",),
        "TGA": ("tga",),
        "TIFF": ("tif", "tiff",),
        "WebP": ("webp",),
        "XBM": ("xbm",),
    }
    RO = {
        "CUR": ("cur",),
        "DCX": ("dcx",),
        "FLI": ("fli", "flc",),
        "FPX": ("fpx",),
        "GBR": ("gbr",),
        "ICO": ("ico",),
        "IPTC/NAA": ("iim",),
        "PCD": ("pcd",),
        "PSD": ("psd",),
        "SGI": ("bw", "rgb", "rgba", "sgi",),
        "XPM": ("xpm",),
    }
    WO = {
        # "PALM": ("palm",),      # doesn't seem to work
        # "PDF": ("pdf",),        # doesn't seem to work
    }


def random_color():
    r = random.randrange(256)
    g = random.randrange(256)
    b = random.randrange(256)
    if r + g + b > 0.7 * 3 * 256:
        r -= 50
        g -= 50
        b -= 50
    return (r, g, b)


class BadPhoto(Exception):
    def __init__(self, photoname):
        self.photoname = photoname


def build_photolist(filelist: [str]) -> [Photo]:
    ret = []

    for name in filelist:
        try:
            img = PIL.Image.open(name)
        except OSError:
            print("Building list --> Skipping a photo: %s" % name)
            continue

        w, h = img.size

        orientation = 0
        try:
            exif = img._getexif()
            if 274 in exif:  # orientation tag
                orientation = exif[274]
                if orientation == 6 or orientation == 8:
                    w, h = h, w
        except Exception:
            pass

        ret.append(Photo(name, w, h, orientation))
    return ret


cache = {}


def paste_photo(canvas, cell, img):
    canvas.paste(img, (int(round(cell.x)), int(round(cell.y))))
    return canvas


class RenderingTask(Thread):
    """Execution thread to do the actual poster rendering

    Image computation is a heavy task, that can take several seconds. During
    this, the program might be unresponsive. To avoid this, rendering is done
    is a separated thread.

    """

    def __init__(self, yearbook_page: Page, page, border_width=0.01, border_color=(0, 0, 0),
                 quality=QUALITY_BEST, output_file=None,
                 on_update=None, on_complete=None, on_fail=None, stitch_background=None):
        super().__init__()

        self.yearbook_page = yearbook_page
        self.page = page
        self.border_width = border_width
        self.border_color = border_color
        self.quality = quality

        self.output_file = output_file

        self.on_update = on_update
        self.on_complete = on_complete
        self.on_fail = on_fail

        self.canceled = False
        self.full_resolution = stitch_background

    def abort(self):
        self.canceled = True

    def draw_skeleton(self, canvas):

        if self.yearbook_page.is_locked():
            return

        for col in self.page.cols:
            for c in col.cells:
                if c.is_extension():
                    continue
                color = random_color()
                x, y, w, h = c.content_coords()
                xy = (x, y)
                xY = (x, y + h - 1)
                Xy = (x + w - 1, y)
                XY = (x + w - 1, y + h - 1)

                draw = PIL.ImageDraw.Draw(canvas)
                draw.line(xy + Xy, fill=color)
                draw.line(xy + xY, fill=color)
                draw.line(xY + XY, fill=color)
                draw.line(Xy + XY, fill=color)
                draw.line(xy + XY, fill=color)
                draw.line(xY + Xy, fill=color)
        return canvas

    def draw_borders(self, canvas):
        if self.yearbook_page.is_locked():
            return

        if self.border_width == 0:
            return

        W = self.page.w - 1
        H = self.page.h - 1
        border = self.border_width - 1
        color = (255, 255, 255, 0)  # self.border_color

        draw = PIL.ImageDraw.Draw(canvas, 'RGBA')
        draw.rectangle((0, 0) + (border, H), color)
        draw.rectangle((W - border, 0) + (W, H), color)
        draw.rectangle((0, 0) + (W, border), color)
        draw.rectangle((0, H - border) + (W, H), color)

        for col in self.page.cols:
            # Draw horizontal borders
            for c in col.cells[1:]:
                xy = (col.x, c.y - border / 2)
                XY = (col.x + col.w, c.y + border / 2)
                draw.rectangle(xy + XY, color)
            # Draw vertical borders
            if col.x > 0:
                for c in col.cells:
                    if not c.is_extension():
                        xy = (col.x - border / 2, c.y)
                        XY = (col.x + border / 2, c.y + c.h)
                        draw.rectangle(xy + XY, color)

        return canvas

    def resize_photo(self, cell, use_cache=False):
        # If a thumbnail is already in cache, let's use it. But only if it is
        # bigger than what we need, because we don't want to lose quality.
        if (use_cache and cell.photo.filename in cache and
                cache[cell.photo.filename].size[0] >= int(round(cell.w)) and
                cache[cell.photo.filename].size[1] >= int(round(cell.h))):
            img = cache[cell.photo.filename].copy()
        else:
            img = PIL.Image.open(cell.photo.filename)

            # Rotate image if EXIF says so
            if cell.photo.orientation == 3:
                img = img.rotate(180, expand=True)
            elif cell.photo.orientation == 6:
                img = img.rotate(270, expand=True)
            elif cell.photo.orientation == 8:
                img = img.rotate(90, expand=True)

        if self.quality == QUALITY_FAST:
            method = PIL.Image.NEAREST
        else:
            method = PIL.Image.ANTIALIAS

        shape = img.size[0] * cell.h - img.size[1] * cell.w
        if shape > 0:  # image is too thick
            img = img.resize((int(round(cell.h * img.size[0] / img.size[1])),
                              int(round(cell.h))), method)
        elif shape < 0:  # image is too tall
            img = img.resize((int(round(cell.w)),
                              int(round(cell.w * img.size[1] / img.size[0]))),
                             method)
        else:
            img = img.resize((int(round(cell.w)), int(round(cell.h))), method)

        # Save this new image to cache (if it is larger than the previous one)
        if (use_cache and (cell.photo.filename not in cache or
                           cache[cell.photo.filename].size[0] < img.size[0])):
            cache[cell.photo.filename] = img

        if shape > 0:  # image is too thick
            width_to_crop = img.size[0] - cell.w
            img = img.crop((
                int(round(width_to_crop * cell.photo.offset_w)),
                0,
                int(round(img.size[0] - width_to_crop *
                          (1 - cell.photo.offset_w))),
                int(round(cell.h))
            ))
        elif shape < 0:  # image is too tall
            height_to_crop = img.size[1] - cell.h
            img = img.crop((
                0,
                int(round(height_to_crop * cell.photo.offset_h)),
                int(round(cell.w)),
                int(round(img.size[1] - height_to_crop *
                          (1 - cell.photo.offset_h)))
            ))

        return img

    def run(self):
        try:
            canvas = PIL.Image.new(
                "RGBA", (int(self.page.w), int(self.page.h)), "black")

            self.draw_skeleton(canvas)
            self.draw_borders(canvas)

            if self.quality != QUALITY_SKEL:
                n = sum([len([cell for cell in col.cells if not
                cell.is_extension()]) for col in self.page.cols])
                i = 0.0
                if self.on_update:
                    self.on_update(canvas, 0.0)
                last_update = time.time()
                pinned_photos = self.yearbook_page.get_all_pinned_photos()
                for col in self.page.cols:
                    for c in col.cells:
                        if self.canceled:  # someone clicked "abort"
                            return

                        if c.is_extension():
                            continue

                        img = self.resize_photo(c, use_cache=True)

                        if not self.full_resolution and c.photo.filename in pinned_photos:
                            img = ImageOps.grayscale(img)

                        paste_photo(canvas, c, img)

                        # Only needed for interactive rendering
                        if self.on_update:
                            self.draw_borders(canvas)

                        i += 1
                        now = time.time()
                        if self.on_update and now > last_update + 0.1:
                            self.on_update(canvas, i / n)
                            last_update = now

                self.draw_borders(canvas)

            if self.output_file:
                print("Saving image at ...", self.output_file)

                if self.full_resolution and self.yearbook_page.personalized:
                    background = PIL.Image.open(self.yearbook_page.image).convert("RGBA")
                    new_background = background.resize(IMAGE_WITH_BLEED_SIZE)
                    if self.yearbook_page.number % 2 != 0:
                        dashed_img_draw = DashedImageDraw(new_background)

                        w, h = TEXT_FONT.getsize(self.yearbook_page.title)

                        dashed_img_draw.dashed_rectangle([(25, 25), (2600, 3350)],
                                                         dash=(5, 4), outline='white', width=2)
                        dashed_img_draw.dashed_rectangle([(75, 75), (2550, 3300)],
                                                         dash=(5, 4), outline='white', width=2)

                        dashed_img_draw.text((int((canvas.size[0] - w) / 2) + 75, 75),
                                             self.yearbook_page.title, (255, 255, 255), font=TEXT_FONT)
                        dashed_img_draw.text((2450, 3200),
                                             str(self.yearbook_page.number),
                                             (255, 255, 255), font=TEXT_FONT_SMALL)

                        new_background.paste(canvas, (75, 175), mask=canvas)
                    else:
                        new_background.paste(canvas, (75, 75), mask=canvas)
                    new_background.save(self.output_file, quality=100)
                else:
                    canvas.save(self.output_file, quality=100)
                    new_background = canvas

            if self.on_complete:
                # We can change this to new_background if we wish to display it with the background
                self.on_complete(new_background, self.output_file)

        except Exception as e:
            if self.on_fail:
                self.on_fail(e)
