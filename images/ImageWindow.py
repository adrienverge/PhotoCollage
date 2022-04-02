import shutil

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Gio, GObject
import gettext

_ = gettext.gettext


class ImageWindow(Gtk.Window):
    def __init__(self, parent_window):
        super().__init__(title=_("Image Viewer"))
        self.add_to_left = Gtk.Button(label=_("Add to left"))
        self.add_to_right = Gtk.Button(label=_("Add to right"))
        self.favorite = Gtk.Button(label=_("Favorite"))
        self.delete = Gtk.Button(label=_("Delete"))
        self.frame = None
        self.image = None
        self.parent_window = parent_window
        self.make_window()

    def make_window(self):
        self.set_border_width(8)

        box_window = Gtk.Box(spacing=10, orientation=Gtk.Orientation.VERTICAL)
        self.add(box_window)

        # ---- Create a box for holding all the buttons ----
        hbox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.HORIZONTAL)
        hbox.set_border_width(8)
        hbox.pack_start(self.add_to_left, False, False, 0)
        hbox.pack_start(self.add_to_right, False, False, 0)
        hbox.pack_start(self.favorite, False, False, 0)
        hbox.pack_end(self.delete, False, False, 0)

        self.add_to_left.connect("clicked", self.add_to_left_pane)
        self.add_to_right.connect("clicked", self.add_to_right_pane)
        self.favorite.connect("clicked", self.add_to_favorites)
        self.delete.connect("clicked", self.delete_image)

        box_window.pack_start(hbox, False, False, 0)

        self.frame = Gtk.Frame()
        self.frame.set_shadow_type(Gtk.ShadowType.IN)

        # The alignment keeps the frame from growing when users resize
        # the window
        align = Gtk.Alignment(xalign=0.5,
                              yalign=0.5,
                              xscale=0,
                              yscale=0)
        align.add(self.frame)
        box_window.pack_start(align, False, False, 0)

    def update_image(self, image):
        print("UPDATING IMAGE %s " % image)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image, 800, 600, True)
        transparent = pixbuf.add_alpha(True, 0xff, 0xff, 0xff)
        new_img = Gtk.Image.new_from_pixbuf(transparent)
        if self.image is not None:
            try:
                self.frame.remove(self.image)
            except:
                pass

        self.frame.add(new_img)
        self.image = image

    def add_to_left_pane(self, widget):
        print(self.parent_window)
        self.parent_window.add_image_to_left_pane(self.image)
        return

    def add_to_right_pane(self, widget):
        print("Image to add %s " % self.image)
        self.parent_window.add_image_to_right_pane(self.image)
        return

    def add_to_favorites(self, widget):
        folder = self.parent_window.get_favorites_folder()
        shutil.copy(self.image, folder)

        # Need to refresh the favorites panel from here
        self.parent_window.update_favorites_images()

    def delete_image(self, widget):
        folder = self.parent_window.get_deleted_images_folder()
        shutil.copy(self.image, folder)
        self.parent_window.add_image_to_deleted(self.image)
        self.parent_window.update_ui_elements()


