# -*- coding: utf-8 -*-
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
    "/8mFbafV794AAAAABJRU5ErkJggg==")


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
