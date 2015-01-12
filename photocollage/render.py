# -*- coding: utf-8 -*-
"""
Copyright (C) 2014 Adrien Vergé

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

from multiprocessing import Process, Pipe
import random
from threading import Thread

import PIL.Image
import PIL.ImageDraw

from photocollage.collage import Photo


QUALITY_SKEL = 0
QUALITY_FAST = 1
QUALITY_BEST = 2


class PIL_SUPPORTED_EXTS(object):
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


def build_photolist(filelist):
    ret = []

    for name in filelist:
        try:
            img = PIL.Image.open(name)
        except IOError:
            raise BadPhoto(name)
        w, h = img.size

        orientation = 0
        try:
            exif = img._getexif()
            if 274 in exif:  # orientation tag
                orientation = exif[274]
                if orientation == 6 or orientation == 8:
                    w, h = h, w
        except:
            pass

        ret.append(Photo(name, w, h, orientation))
    return ret


class RenderingFailed(Exception):
    pass


class RenderingCanceled(Exception):
    pass


class RenderingProcess(Process):
    """Perform actual computation and return the image

    RenderingProcess is given a function to execute (to render an image), and
    returns what it is asked to (whether the raw image, or nothing).

    """
    def __init__(self, rd_conn, wr_conn, fn, *args, **kwargs):
        super(RenderingProcess, self).__init__()

        self.rd_conn = rd_conn
        self.wr_conn = wr_conn
        self.fn = fn
        self.fn_args = args
        self.fn_kwargs = kwargs

    def run(self):
        # Close the unused pipe ends
        self.rd_conn.close()

        self.wr_conn.send(self.fn(*self.fn_args, **self.fn_kwargs))
        self.wr_conn.close()


class RenderingTask(Thread):
    """Execution thread to do the actual poster rendering

    Image computation is a heavy task, that can take several seconds. During
    this, the program might be unresponding. To avoid this, rendering is done
    is a separated thread. More precisely, this threads spawns other processes
    (because of the GIL, threads are not real threads in Python) for actually
    heavy tasks (scaling input images). Besides, creating a new process make it
    possible to stop an already began calculation by killing the process.

    """
    def __init__(self, page, border_width=0.02, border_color=(0, 0, 0),
                 quality=QUALITY_FAST, output_file=None, interactive=False,
                 on_update=None, on_complete=None, on_fail=None):
        super(RenderingTask, self).__init__()

        self.page = page
        self.border_width = border_width
        self.border_color = border_color
        self.quality = quality

        self.on_update = on_update
        self.on_complete = on_complete
        self.on_fail = on_fail

        self.processes = []
        self.canceled = False

    def do_in_subprocess(self, fn, *fn_args, **fn_kwargs):
        rd_conn, wr_conn = Pipe(False)
        process = RenderingProcess(rd_conn, wr_conn,
                                   fn, *fn_args, **fn_kwargs)
        self.processes.append(process)
        process.start()
        wr_conn.close()

        try:
            output = rd_conn.recv()
            rd_conn.close()
            return output
        # except EOFError:
        #     # In case the process was terminated abruptly
        except:
            rd_conn.close()
            if self.canceled:
                raise RenderingCanceled()
            raise RenderingFailed()

    def abort(self):
        self.canceled = True
        for process in self.processes:
            process.terminate()

    def draw_skeleton(self, canvas):
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
        W = self.page.w - 1
        H = self.page.h - 1
        border = self.border_width - 1
        color = self.border_color

        draw = PIL.ImageDraw.Draw(canvas)
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

    def resize_photo(self, cell, raw_output=False):
        img = PIL.Image.open(cell.photo.filename)

        # Rotate image is EXIF says so
        if cell.photo.orientation == 3:
            img = img.rotate(180)
        elif cell.photo.orientation == 6:
            img = img.rotate(270)
        elif cell.photo.orientation == 8:
            img = img.rotate(90)

        if self.quality == QUALITY_FAST:
            method = PIL.Image.NEAREST
        else:
            method = PIL.Image.ANTIALIAS

        if img.size[0] * cell.h > img.size[1] * cell.w:
            # Image is too thick
            img = img.resize((int(round(cell.h * img.size[0] / img.size[1])),
                              int(round(cell.h))), method)
            img = img.crop(
                (int(round((img.size[0] - cell.w) / 2)), 0,
                 int(round((img.size[0] + cell.w) / 2)), int(round(cell.h))))
        elif img.size[0] * cell.h < img.size[1] * cell.w:
            # Image is too tall
            img = img.resize((int(round(cell.w)),
                              int(round(cell.w * img.size[1] / img.size[0]))),
                             method)
            img = img.crop(
                (0, int(round((img.size[1] - cell.h) / 2)),
                 int(round(cell.w)), int(round((img.size[1] + cell.h) / 2))))
        else:
            img = img.resize((int(round(cell.w)), int(round(cell.h))), method)

        # Cannot return the PIL.Image object because it seems not to be handled
        # by pickle, so not passable through a multiprocessing pipe.
        # So we use this trick:
        if raw_output:
            return img.size[0], img.size[1], img.tostring()
        return img

    def paste_photo(self, canvas, cell, img):
        canvas.paste(img, (int(round(cell.x)), int(round(cell.y))))
        return canvas


class BatchRenderingTask(RenderingTask):
    def __init__(self, output_file, *args, **kwargs):
        super(BatchRenderingTask, self).__init__(*args, **kwargs)
        self.output_file = output_file

    def compose_and_save_poster(self, page, output_file):
        canvas = PIL.Image.new(
            "RGB", (int(page.w), int(page.h)), "white")

        for col in page.cols:
            for c in col.cells:
                if c.is_extension():
                    continue
                img = self.resize_photo(c)
                self.paste_photo(canvas, c, img)
        self.draw_borders(canvas)

        canvas.save(output_file)

    def run(self):
        try:
            self.do_in_subprocess(self.compose_and_save_poster, self.page,
                                  self.output_file)
            if self.on_complete:
                self.on_complete()
        except RenderingCanceled:
            pass
        except:
            if self.on_fail:
                self.on_fail()


class InteractiveRenderingTask(RenderingTask):
    def run(self):
        try:
            canvas = PIL.Image.new(
                "RGB", (int(self.page.w), int(self.page.h)), "white")

            self.draw_skeleton(canvas)
            self.draw_borders(canvas)

            if self.quality != QUALITY_SKEL:
                n = sum([len([cell for cell in col.cells if not
                              cell.is_extension()]) for col in self.page.cols])
                i = 0.0
                for col in self.page.cols:
                    for c in col.cells:
                        if c.is_extension():
                            continue
                        w, h, raw = self.do_in_subprocess(
                            self.resize_photo, c, raw_output=True)
                        img = PIL.Image.fromstring("RGB", (w, h), raw)
                        self.paste_photo(canvas, c, img)
                        self.draw_borders(canvas)

                        if self.on_update:
                            i += 1
                            self.on_update(canvas, i / n)

            if self.on_complete:
                self.on_complete(canvas)
        except RenderingCanceled:
            pass
        except:
            if self.on_fail:
                self.on_fail()
