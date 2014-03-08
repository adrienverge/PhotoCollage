PhotoCollage
============

*Graphical tool to make photo collage posters*

PhotoCollage allows you to create photo collage posters.  It assembles the
input photographs you give it to generate a big poster.  Photos are arranged
to fill the whole poster, however you can influence the algorithm to change the
final layout.  You can also set a custom border between photos, and save the
generated image in the resolution you want.

The algorithm generates random layouts that place photos while taking advantage
of all free space.  It tries to fill all space while keeping each photo as
large as possible.

PhotoCollage does more or less the same as many commercial websites do, but
for free and with open-source code.

![screenshot](https://github.com/adrienverge/PhotoCollage/raw/master/screenshots/photocollage-1.0-preview.png)

It provides a library to create photo layouts and posters, and a GTK graphical
user interface.  PhotoCollage is written in Python (compatible with versions 2
and 3) and requires the Python Imaging Library (PIL).

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
[zip archive](https://github.com/adrienverge/PhotoCollage/archive/master.zip)
or clone the
[git repository](https://github.com/adrienverge/PhotoCollage.git).

Usage
-----

Simply run:
```
./photocollage
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
