PhotoCollage
============

*Graphical tool to make photo collage posters*

PhotoCollage allows you to create photo collage posters. It assembles the input
photographs it is given to generate a big poster. Photos are automatically
arranged to fill the whole poster, then you can change the final layout,
dimensions, border or swap photos in the generated grid. Eventually the final
poster image can we saved in any size.

The algorithm generates random layouts that place photos while taking advantage
of all free space. It tries to fill all space while keeping each photo as
large as possible.

PhotoCollage does more or less the same as many commercial websites do, but
for free and with open-source code.

![screenshot](https://github.com/adrienverge/PhotoCollage/raw/v1.2.0/screenshots/photocollage-1.2-preview.png)

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
* available in English and French

Installation
------------

* Fedora:
  ```
  sudo yum install photocollage
  ```

* Ubuntu:
  ```
  sudo add-apt-repository ppa:dhor/myway && sudo apt-get update
  sudo apt-get install photocollage
  ```

* Using pip (for other OS):
  ```
  sudo pip3 install photocollage  # you may need to use python3-pip instead of pip3
  ```

* Manual installation (for other OS):
  ```
  # Install dependencies
  sudo yum install python3-pillow python3-gobject python3-distutils-extra
  sudo apt-get install python3-pil python3-gi python3-distutils-extra
  sudo pacman -S python-pillow python-gobject python-distutils-extra
  # Install PhotoCollage
  git clone https://github.com/adrienverge/PhotoCollage.git
  cd PhotoCollage
  sudo python3 setup.py install
  ```

Usage
-----

After install a launcher for PhotoCollage will appear in your desktop menu.

If it doesn't, just run the command:
```
photocollage
```
