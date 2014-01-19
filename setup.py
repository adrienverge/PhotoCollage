#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Adrien Vergé

from distutils.core import setup

from photopostergeneratorlib.version import APP_NAME, APP_VERSION

long_description = """Photo Poster Generator allows you to create a poster composed from many input photographs.  The ways photos are arranged is optimized to fill the whole poster, however you can influence the layout.  You can also set a custom border between photos."""

setup(
    name = APP_NAME,
	version = APP_VERSION,
    author = "Adrien Vergé",
    author_email = "dont@sp.am",
    url = "https://github.com/adrienverge/photopostergenerator",
    description = "A simple tool to make a big poster with several photos",
    long_description = long_description,
    license = "GPLv2",
    platforms = ["linux"],

    classifiers = [
        "Development Status :: 5 - Production/Stable",
		"Environment :: X11 Applications :: GTK",
		"Intended Audience :: End Users/Desktop",
		"License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.4",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
		"Topic :: Multimedia :: Graphics",
        ],

	packages = ["photopostergeneratorlib"],
    scripts = ["photopostergenerator"],
	data_files = [
		("share/doc/" + APP_NAME + "-" + APP_VERSION, ["README.md","LICENSE"]),
		("share/applications", ["photopostergenerator.desktop"]),
		("share/pixmaps", ["pixmaps/photopostergenerator.png"]),
		("share/locale/fr/LC_MESSAGES",
			["locale/fr/LC_MESSAGES/photopostergenerator.mo"]),
	],

	requires = [
		"copy",
		"gi.repository.Gdk",
		"gi.repository.GdkPixbuf",
		"gi.repository.GObject",
		"gi.repository.Gtk",
		"io.BytesIO",
		"math",
		"multiprocessing.Pipe",
		"multiprocessing.Process",
		"os.path",
		"PIL.Image",
		"PIL.ImageDraw",
		"random",
		"threading.Thread",
	],
    )
