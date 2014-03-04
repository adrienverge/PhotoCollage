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
* generate random new layouts until one suits the user
* choose border color and width
* save high-resolution image
* works even with a large number of photos (> 100)
* integrates into the GNOME environment
* available in English and French

Download
--------

Download the latest version in a
[zip archive](https://github.com/adrienverge/photopostergenerator/archive/master.zip)
or clone the
[git repository](https://github.com/adrienverge/photopostergenerator.git).

Usage
-----

Simply run:
```
./photopostergenerator
```

If it doesn't work, maybe you'll need to install the dependencies.

On Fedora:
```
sudo yum install python3-pillow python3-gobject
```

On Debian/Ubuntu:
```
sudo apt-get install python-pil python3-gi
```

On Arch Linux:
```
sudo pacman -S python-pillow python-gobject
```

Installation
------------

To install it on your system, run:
```
sudo python3 setup.py install
```

RPM and DEB packages to come...
