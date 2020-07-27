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

import base64
from io import BytesIO

import cairo
from gi.repository import GdkPixbuf


# Generated with:
#   import base64
#   with open("data/icons/dragndrop.png", "rb") as f:
#       encoded_image = base64.b64encode(f.read())
#   n = 79 - 4 - 2
#   for i in range(0, len(encoded_image), n):
#       print('    "' + encoded_image[i:i+n].decode('ascii') + '"')
ICON_DRAG_AND_DROP = (
    "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"
    "U4Z3kUZTSagAAAAASUVORK5CYII=")


def load_pixbuf(encoded):
    loader = GdkPixbuf.PixbufLoader.new_with_type("png")
    loader.write(base64.b64decode(encoded))
    loader.close()
    return loader.get_pixbuf()


def load_cairo_surface(encoded):
    buf = BytesIO()
    buf.write(base64.b64decode(encoded))
    buf.seek(0)
    surface = cairo.ImageSurface.create_from_png(buf)
    buf.close()
    return surface
