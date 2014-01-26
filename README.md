Photo Poster Generator
======================

Photo Poster Generator is an application to make posters out of multiple
photos.  It generates random layouts that place photos while taking advantage
of all free space.  The algorithm tries to fill all space and keep each
photo as large as possible.

![screenshot](https://raw.github.com/adrienverge/photopostergenerator/master/screenshot.png)

It provides a library to create photo layouts and posters, and a GTK graphical
user interface.  Photo Poster Generator is written in Python (compatible with
versions 2 and 3) and requires the Python Imaging Library (PIL).

Features:
* allows the user to create new layouts until the right one appears
* works even with a large number of images (> 100)
* integrates into the GNOME environment

Usage
-----

Download the zip archive or clone the git repository, then run:
```
./photopostergenerator
```

If it doesn't work, maybe you'll need to install the dependencies.

On Debian/Ubuntu:
```
sudo apt-get install python-pil python-gtk2
```

On Fedora:
```
sudo yum install python-pillow pygtk2
```

Installation
------------

To install it on your system, run:
```
sudo python setup.py install
```

RPM and DEB packages to come...
