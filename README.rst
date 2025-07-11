PhotoCollage
============

.. image::
   https://travis-ci.org/adrienverge/PhotoCollage.svg?branch=master
   :target: https://travis-ci.org/adrienverge/PhotoCollage
   :alt: CI tests status

*Graphical tool to make photo collage posters*

PhotoCollage allows you to create photo collage posters. It assembles the input
photographs it is given to generate a big poster. Photos are automatically
arranged to fill the whole poster, then you can change the final layout,
dimensions, border or swap photos in the generated grid. Eventually the final
poster image can be saved in any size.

The algorithm generates random layouts that place photos while taking advantage
of all free space. It tries to fill all space while keeping each photo as
large as possible.

PhotoCollage does more or less the same as many commercial websites do, but
for free and with open-source code.

.. image::
   screenshots/photocollage-1.4-preview.png
   :alt: screenshot

It provides a library to create photo layouts and posters, and a GTK graphical
user interface. PhotoCollage is written in Python (compatible with versions 2
and 3) and requires the Python Imaging Library (PIL).

Features:

* generate random new layouts until one suits the user
* choose border color and width
* possible to swap photos in the generated grid
* save high-resolution image
* works even with a large number of photos (> 100)
* integrates into the GNOME environment
* available in English, French, German, Czech, Italian, Bulgarian, Dutch, Russian, Spanish, Polish and Ukrainian

Installation
------------

* Fedora 19+:

  .. code:: bash

   sudo dnf install photocollage

* Debian 9+ / Ubuntu 16.10+:

  .. code:: bash

   sudo apt-get install photocollage

* Using pip, the Python package manager:

  .. code:: bash

   sudo pip3 install photocollage

Usage
-----

After install a launcher for PhotoCollage will appear in your desktop menu.

If it doesn't, just run the command:

.. code:: bash

 photocollage

Hacking
-------

* If you changed the source and want to test your modifications, run:

  .. code:: bash

   python -c 'from photocollage import gtkgui; gtkgui.main()'

* If you need to build a package from source and install it:

  .. code:: bash

   # Install dependencies
   sudo dnf install python3-pillow python3-gobject
   sudo apt-get install python3-pil python3-gi
   sudo pacman -S python-pillow python-gobject

   # Install PhotoCollage
   python -m build
   pip install --user --upgrade dist/photocollage-*.tar.gz

* If you wish to contribute, please lint your code and pass tests:

  .. code:: bash

   flake8 .
   python -m unittest tests/test_*.py
