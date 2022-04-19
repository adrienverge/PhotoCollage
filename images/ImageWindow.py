import shutil

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Gio, GObject
import gettext
import os

_ = gettext.gettext


class ImageWindow(Gtk.Window):

    def __init__(self, parent_window):
        super().__init__(title=_("Image Viewer"))
        self.add_to_left = Gtk.Button(label=_("Add to left"))
        self.add_to_right = Gtk.Button(label=_("Add to right"))
        self.next = Gtk.Button(label=_("Next"))
        self.prev = Gtk.Button(label=_("Prev"))
        self.favorite = Gtk.ToggleButton(label=_("Favorite"))
        self.unfavorite = Gtk.ToggleButton(label=_("UnFavorite"))

        self.delete = Gtk.Button(label=_("Delete"))
        self.frame = None
        self.current_image = None
        self.parent_window = parent_window
        self.browse_images_list = []
        self.make_window()
        self.connect('delete-event', self.ignore)

    def update_images_list(self, images):
        self.browse_images_list = images

    def ignore(self, widget=None, *data):  # do nothing
        return True

    @property
    def favorites(self):
        favorites_folder = self.parent_window.get_favorites_folder()
        if favorites_folder is not None:
            return [os.path.join(favorites_folder, img) for img in os.listdir(favorites_folder)]

        return None

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
        hbox.pack_start(self.unfavorite, False, False, 0)
        hbox.pack_start(self.prev, False, False, 0)
        hbox.pack_start(self.next, False, False, 0)

        hbox.pack_end(self.delete, False, False, 0)

        self.add_to_left.connect("clicked", self.add_to_left_pane)
        self.add_to_right.connect("clicked", self.add_to_right_pane)
        self.favorite.connect("clicked", self.add_to_favorites)
        self.unfavorite.connect("clicked", self.remove_from_favorites)

        self.prev.connect("clicked", self.prev_image)
        self.next.connect("clicked", self.next_image)

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
        if not os.path.exists(image):
            print("%s does not exist" % image)
            return

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image, 800, 600, True)
        transparent = pixbuf.add_alpha(True, 0xff, 0xff, 0xff)
        new_img = Gtk.Image.new_from_pixbuf(transparent)

        [self.frame.remove(child) for child in self.frame.get_children()]
        self.frame.add(new_img)

        self.current_image = image
        self.frame.show_all()
        self.update_buttons()
        self.set_keep_above(True)  # if used alone it will cause window permanently on top
        self.show_all()  # show your window, should be in the middle between these 2 calls
        self.set_keep_above(False)  # disable always on top

    def add_to_left_pane(self, widget):

        self.parent_window.add_image_to_left_pane(self.current_image)

        self.add_to_left.set_sensitive(False)
        self.add_to_right.set_sensitive(False)
        return

    def add_to_right_pane(self, widget):
        self.parent_window.add_image_to_right_pane(self.current_image)
        self.add_to_left.set_sensitive(False)
        self.add_to_right.set_sensitive(False)
        return

    def update_buttons(self):
        if self.current_image is not None:
            self.favorite.set_active(self.current_image in self.favorites)
            self.unfavorite.set_active(not(self.current_image in self.favorites))

        self.add_to_left.set_sensitive(not self.parent_window.is_left_page_locked())
        self.add_to_right.set_sensitive(not self.parent_window.is_right_page_locked())

    def add_to_favorites(self, widget):

        self.parent_window.favorite_images.add(self.current_image)
        # Need to refresh the favorite panel from here
        self.parent_window.update_favorites_images()
        self.update_buttons()

    def remove_from_favorites(self, widget):
        try:
            self.parent_window.favorite_images.remove(self.current_image)
        except KeyError:
            pass

        self.parent_window.update_favorites_images()
        self.update_buttons()

    def delete_image(self, widget):
        folder = self.parent_window.get_deleted_images_folder()
        shutil.copy(self.current_image, folder)
        self.parent_window.add_image_to_deleted(self.current_image)
        self.parent_window.update_ui_elements()

    def next_image(self, widget):
        try:
            index = self.browse_images_list.index(self.current_image)
            new_img = self.browse_images_list[index+1]
        except ValueError:
            new_img = self.browse_images_list[0]
        except IndexError:
            new_img = self.browse_images_list[-1]

        if os.path.exists(new_img):
            self.update_image(new_img)

    def prev_image(self, widget):
        try:
            index = self.browse_images_list.index(self.current_image)
            new_img = self.browse_images_list[index-1]
        except ValueError:
            new_img = self.browse_images_list[0]
        except IndexError:
            new_img = self.browse_images_list[0]

        if os.path.exists(new_img):
            self.update_image(new_img)
