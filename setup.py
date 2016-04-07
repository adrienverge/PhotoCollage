#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Adrien Vergé
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

from distutils.core import setup

from DistUtilsExtra.command import build_extra, build_i18n

from photocollage import APP_NAME, APP_VERSION


long_description = (
    "PhotoCollage allows you to create photo collage posters. It assembles "
    "the input photographs it is given to generate a big poster. Photos are "
    "automatically arranged to fill the whole poster, then you can change the "
    "final layout, dimensions, border or swap photos in the generated grid. "
    "Eventually the final poster image can we saved in any size.")

setup(
    name=APP_NAME,
    version=APP_VERSION,
    author="Adrien Vergé",
    author_email="adrienverge@gmail.com",
    url="https://github.com/adrienverge/PhotoCollage",
    description="Graphical tool to make photo collage posters",
    long_description=long_description,
    license="GPLv2+",
    platforms=["linux"],

    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved"
        " :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Multimedia :: Graphics",
    ],

    packages=["photocollage"],
    scripts=["bin/photocollage"],
    data_files=[
        ("share/applications", ["data/photocollage.desktop"]),
        ("share/appdata", ["data/photocollage.appdata.xml"]),
        ("share/icons/hicolor/scalable/apps",
         ["data/icons/hicolor/scalable/apps/photocollage.svg"]),
        ("share/icons/hicolor/16x16/apps",
         ["data/icons/hicolor/16x16/apps/photocollage.png"]),
        ("share/icons/hicolor/22x22/apps",
         ["data/icons/hicolor/22x22/apps/photocollage.png"]),
        ("share/icons/hicolor/24x24/apps",
         ["data/icons/hicolor/24x24/apps/photocollage.png"]),
        ("share/icons/hicolor/32x32/apps",
         ["data/icons/hicolor/32x32/apps/photocollage.png"]),
        ("share/icons/hicolor/48x48/apps",
         ["data/icons/hicolor/48x48/apps/photocollage.png"]),
        ("share/icons/hicolor/64x64/apps",
         ["data/icons/hicolor/64x64/apps/photocollage.png"]),
        ("share/icons/hicolor/128x128/apps",
         ["data/icons/hicolor/128x128/apps/photocollage.png"]),
        ("share/icons/hicolor/256x256/apps",
         ["data/icons/hicolor/256x256/apps/photocollage.png"]),
    ],

    cmdclass={
        "build": build_extra.build_extra,
        "build_i18n": build_i18n.build_i18n
    },

    requires=[
        "Pillow",
        "pycairo",
        # Also requires PyGI (the Python GObject Introspection bindings), which
        # is not packaged on pypi.
    ],
)
